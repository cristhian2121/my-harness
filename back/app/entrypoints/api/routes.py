from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.application.exceptions import (
    AgentUnavailableError,
    DocumentAccessError,
    DocumentNotFoundError,
    DocumentProcessingError,
    EmptyDocumentError,
    InvalidUserCredentialsError,
    InvalidDocumentRequestError,
    UnsupportedDocumentFormatError,
    UnsafePromptError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.application.use_cases import (
    AskUseCase,
    AskDocumentsUseCase,
    GetDocumentDetailUseCase,
    GetHistoryUseCase,
    HealthUseCase,
    InitUserUseCase,
    IngestDocumentUseCase,
    ListDocumentsUseCase,
    ValidateUserUseCase,
)
from app.core.container import AppContainer
from app.domain.entities import Document
from app.entrypoints.api.dependencies import get_container, get_db_session
from app.entrypoints.api.schemas import (
    AskRequest,
    AskResponse,
    DocumentListResponse,
    DocumentQuestionRequest,
    DocumentQuestionResponse,
    DocumentResponse,
    DocumentSourceResponse,
    ErrorResponse,
    HealthResponse,
    HistoryItemResponse,
    HistoryResponse,
    InitUserRequest,
    InitUserResponse,
    UserResponse,
    ValidateUserRequest,
    ValidateUserResponse,
)
from app.infrastructure.repositories import (
    SqlAlchemyChatRepository,
    SqlAlchemyDocumentChunkRepository,
    SqlAlchemyDocumentRepository,
    SqlAlchemyUserRepository,
)

router = APIRouter()


@router.post(
    "/init_user",
    response_model=InitUserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "User already exists."},
    },
)
def init_user(
    payload: InitUserRequest,
    container: AppContainer = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> InitUserResponse:
    use_case = InitUserUseCase(SqlAlchemyUserRepository(session))
    try:
        user = use_case.execute(username=payload.username, role=payload.role)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return InitUserResponse(
        message="User created successfully.",
        user=UserResponse(
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/validate_user",
    response_model=ValidateUserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Username and role do not match."},
    },
)
def validate_user(
    payload: ValidateUserRequest,
    session: Session = Depends(get_db_session),
) -> ValidateUserResponse:
    use_case = ValidateUserUseCase(SqlAlchemyUserRepository(session))
    try:
        user = use_case.execute(username=payload.username, role=payload.role)
    except InvalidUserCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ValidateUserResponse(
        message="User validated successfully.",
        user=UserResponse(
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Request blocked by policy."},
        404: {"model": ErrorResponse, "description": "User was not found."},
        503: {"model": ErrorResponse, "description": "AI agent unavailable."},
    },
)
async def ask(
    payload: AskRequest,
    container: AppContainer = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> AskResponse:
    use_case = AskUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        chat_repository=SqlAlchemyChatRepository(session),
        chat_agent=container.chat_agent,
        validate_prompt=container.security_filter.validate,
    )
    try:
        interaction = await use_case.execute(
            username=payload.username,
            message=payload.message,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnsafePromptError as exc:
        return AskResponse(
            username=payload.username,
            message=payload.message,
            response=str(exc),
            status="blocked",
            created_at=None,
        )
    except AgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return AskResponse(
        username=interaction.username,
        message=interaction.message,
        response=interaction.response,
        status=interaction.status.value,
        created_at=interaction.created_at,
    )


@router.get(
    "/history/{username}",
    response_model=HistoryResponse,
    responses={404: {"model": ErrorResponse, "description": "User was not found."}},
)
def history(
    username: str,
    session: Session = Depends(get_db_session),
) -> HistoryResponse:
    use_case = GetHistoryUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        chat_repository=SqlAlchemyChatRepository(session),
    )
    try:
        items = use_case.execute(username=username)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return HistoryResponse(
        username=username,
        items=[
            HistoryItemResponse(
                message=item.message,
                response=item.response,
                status=item.status.value,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or unsupported document."},
        404: {"model": ErrorResponse, "description": "User was not found."},
    },
)
async def upload_document(
    username: str = Form(...),
    file: UploadFile = File(...),
    container: AppContainer = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> DocumentResponse:
    use_case = IngestDocumentUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        chunk_repository=SqlAlchemyDocumentChunkRepository(session),
        storage=container.document_storage,
        parser=container.document_parser,
        embedding_service=container.embedding_service,
        vector_store=container.vector_store,
    )
    try:
        document = use_case.execute(
            username=username,
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            content=await file.read(),
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        UnsupportedDocumentFormatError,
        EmptyDocumentError,
        DocumentProcessingError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_document(document)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    responses={404: {"model": ErrorResponse, "description": "User was not found."}},
)
def list_documents(
    username: str = Query(..., min_length=3, max_length=100),
    session: Session = Depends(get_db_session),
) -> DocumentListResponse:
    use_case = ListDocumentsUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
    )
    try:
        documents = use_case.execute(username=username)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DocumentListResponse(
        username=username,
        items=[_serialize_document(document) for document in documents],
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Document does not belong to the user."},
        404: {"model": ErrorResponse, "description": "Document or user not found."},
    },
)
def get_document_detail(
    document_id: str,
    username: str = Query(..., min_length=3, max_length=100),
    session: Session = Depends(get_db_session),
) -> DocumentResponse:
    use_case = GetDocumentDetailUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
    )
    try:
        document = use_case.execute(username=username, document_id=document_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _serialize_document(document)


@router.post(
    "/documents/ask",
    response_model=DocumentQuestionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid document question request."},
        403: {"model": ErrorResponse, "description": "Document does not belong to the user."},
        404: {"model": ErrorResponse, "description": "User or document not found."},
        503: {"model": ErrorResponse, "description": "AI agent unavailable."},
    },
)
async def ask_documents(
    payload: DocumentQuestionRequest,
    container: AppContainer = Depends(get_container),
    session: Session = Depends(get_db_session),
) -> DocumentQuestionResponse:
    use_case = AskDocumentsUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        vector_store=container.vector_store,
        embedding_service=container.embedding_service,
        chat_agent=container.chat_agent,
        validate_prompt=container.security_filter.validate,
    )
    try:
        answer = await use_case.execute(
            username=payload.username,
            question=payload.question,
            document_ids=payload.document_ids,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidDocumentRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnsafePromptError as exc:
        return DocumentQuestionResponse(
            username=payload.username,
            question=payload.question,
            answer=str(exc),
            status="blocked",
            document_ids=payload.document_ids,
            sources=[],
        )
    except AgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return DocumentQuestionResponse(
        username=answer.username,
        question=answer.question,
        answer=answer.answer,
        status=answer.status.value,
        document_ids=answer.document_ids,
        sources=[
            DocumentSourceResponse(
                chunk_id=source.chunk_id,
                document_id=source.document_id,
                filename=source.filename,
                snippet=source.text,
                score=source.score,
                chunk_index=source.chunk_index,
                page_number=source.page_number,
                sheet_name=source.sheet_name,
                row_start=source.row_start,
                row_end=source.row_end,
            )
            for source in answer.sources
        ],
    )


@router.get("/health", response_model=HealthResponse)
async def health(container: AppContainer = Depends(get_container)) -> HealthResponse:
    use_case = HealthUseCase(
        session_factory=container.session_factory,
        chat_agent=container.chat_agent,
    )
    result = await use_case.execute()
    return HealthResponse.model_validate(result)


def _serialize_document(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        username=document.username,
        filename=document.filename,
        content_type=document.content_type,
        extension=document.extension,
        size_bytes=document.size_bytes,
        checksum_sha256=document.checksum_sha256,
        status=document.status.value,
        chunk_count=document.chunk_count,
        page_count=document.page_count,
        row_count=document.row_count,
        sheet_names=document.sheet_names,
        error_detail=document.error_detail,
        created_at=document.created_at,
    )
