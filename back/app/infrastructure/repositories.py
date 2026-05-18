from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import ChatInteraction, Document, DocumentChunk, User
from app.infrastructure.db.models import (
    ChatMessageModel,
    DocumentChunkModel,
    DocumentModel,
    UserModel,
)


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user: User) -> User:
        record = UserModel(username=user.username, role=user.role)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return User(
            username=record.username,
            role=record.role,
            created_at=record.created_at,
        )

    def get_by_username(self, username: str) -> User | None:
        statement = select(UserModel).where(UserModel.username == username)
        record = self._session.execute(statement).scalar_one_or_none()
        if record is None:
            return None
        return User(
            username=record.username,
            role=record.role,
            created_at=record.created_at,
        )


class SqlAlchemyChatRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, interaction: ChatInteraction) -> ChatInteraction:
        user_record = self._session.execute(
            select(UserModel).where(UserModel.username == interaction.username)
        ).scalar_one()
        record = ChatMessageModel(
            user_id=user_record.id,
            message=interaction.message,
            response=interaction.response,
            status=interaction.status,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return ChatInteraction(
            username=interaction.username,
            message=record.message,
            response=record.response,
            status=record.status,
            created_at=record.created_at,
        )

    def get_history(self, username: str) -> list[ChatInteraction]:
        statement = (
            select(ChatMessageModel, UserModel.username)
            .join(UserModel, ChatMessageModel.user_id == UserModel.id)
            .where(UserModel.username == username)
            .order_by(ChatMessageModel.created_at.asc(), ChatMessageModel.id.asc())
        )
        rows = self._session.execute(statement).all()
        return [
            ChatInteraction(
                username=row.username,
                message=row.ChatMessageModel.message,
                response=row.ChatMessageModel.response,
                status=row.ChatMessageModel.status,
                created_at=row.ChatMessageModel.created_at,
            )
            for row in rows
        ]


class SqlAlchemyDocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, document: Document) -> Document:
        user_record = self._session.execute(
            select(UserModel).where(UserModel.username == document.username)
        ).scalar_one()
        record = DocumentModel(
            id=document.id,
            user_id=user_record.id,
            filename=document.filename,
            content_type=document.content_type,
            extension=document.extension,
            size_bytes=document.size_bytes,
            checksum_sha256=document.checksum_sha256,
            storage_path=document.storage_path,
            status=document.status,
            chunk_count=document.chunk_count,
            page_count=document.page_count,
            row_count=document.row_count,
            sheet_names=json.dumps(document.sheet_names) if document.sheet_names else None,
            error_detail=document.error_detail,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._to_entity(record, document.username)

    def update(self, document: Document) -> Document:
        record = self._session.execute(
            select(DocumentModel)
            .join(UserModel, DocumentModel.user_id == UserModel.id)
            .where(DocumentModel.id == document.id, UserModel.username == document.username)
        ).scalar_one()
        record.filename = document.filename
        record.content_type = document.content_type
        record.extension = document.extension
        record.size_bytes = document.size_bytes
        record.checksum_sha256 = document.checksum_sha256
        record.storage_path = document.storage_path
        record.status = document.status
        record.chunk_count = document.chunk_count
        record.page_count = document.page_count
        record.row_count = document.row_count
        record.sheet_names = json.dumps(document.sheet_names) if document.sheet_names else None
        record.error_detail = document.error_detail
        self._session.commit()
        self._session.refresh(record)
        return self._to_entity(record, document.username)

    def list_by_username(self, username: str) -> list[Document]:
        statement = (
            select(DocumentModel, UserModel.username)
            .join(UserModel, DocumentModel.user_id == UserModel.id)
            .where(UserModel.username == username)
            .order_by(DocumentModel.created_at.desc(), DocumentModel.id.desc())
        )
        rows = self._session.execute(statement).all()
        return [self._to_entity(row.DocumentModel, row.username) for row in rows]

    def get_by_id(self, document_id: str) -> Document | None:
        row = self._session.execute(
            select(DocumentModel, UserModel.username)
            .join(UserModel, DocumentModel.user_id == UserModel.id)
            .where(DocumentModel.id == document_id)
        ).one_or_none()
        if row is None:
            return None
        return self._to_entity(row.DocumentModel, row.username)

    @staticmethod
    def _to_entity(record: DocumentModel, username: str) -> Document:
        sheet_names = json.loads(record.sheet_names) if record.sheet_names else None
        return Document(
            id=record.id,
            username=username,
            filename=record.filename,
            content_type=record.content_type,
            extension=record.extension,
            size_bytes=record.size_bytes,
            checksum_sha256=record.checksum_sha256,
            storage_path=record.storage_path,
            status=record.status,
            chunk_count=record.chunk_count,
            page_count=record.page_count,
            row_count=record.row_count,
            sheet_names=sheet_names,
            error_detail=record.error_detail,
            created_at=record.created_at,
        )


class SqlAlchemyDocumentChunkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        records = [
            DocumentChunkModel(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                page_number=chunk.page_number,
                sheet_name=chunk.sheet_name,
                row_start=chunk.row_start,
                row_end=chunk.row_end,
                metadata_json=json.dumps(chunk.metadata) if chunk.metadata else None,
            )
            for chunk in chunks
        ]
        self._session.add_all(records)
        self._session.commit()
        for record in records:
            self._session.refresh(record)
        return [
            DocumentChunk(
                id=record.id,
                document_id=record.document_id,
                chunk_index=record.chunk_index,
                text=record.text,
                page_number=record.page_number,
                sheet_name=record.sheet_name,
                row_start=record.row_start,
                row_end=record.row_end,
                metadata=json.loads(record.metadata_json) if record.metadata_json else None,
                created_at=record.created_at,
            )
            for record in records
        ]
