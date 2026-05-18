from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import ChatInteraction, User
from app.infrastructure.db.models import ChatMessageModel, UserModel


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
