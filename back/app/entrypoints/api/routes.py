from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.exceptions import (
    AgentUnavailableError,
    InvalidUserCredentialsError,
    UnsafePromptError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.application.use_cases import (
    AskUseCase,
    GetHistoryUseCase,
    HealthUseCase,
    InitUserUseCase,
    ValidateUserUseCase,
)
from app.core.container import AppContainer
from app.entrypoints.api.dependencies import get_container, get_db_session
from app.entrypoints.api.schemas import (
    AskRequest,
    AskResponse,
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


@router.get("/health", response_model=HealthResponse)
async def health(container: AppContainer = Depends(get_container)) -> HealthResponse:
    use_case = HealthUseCase(
        session_factory=container.session_factory,
        chat_agent=container.chat_agent,
    )
    result = await use_case.execute()
    return HealthResponse.model_validate(result)
