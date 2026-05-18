from __future__ import annotations

from typing import Protocol

from app.domain.entities import ChatInteraction, User


class UserRepository(Protocol):
    def create(self, user: User) -> User:
        ...

    def get_by_username(self, username: str) -> User | None:
        ...


class ChatRepository(Protocol):
    def create(self, interaction: ChatInteraction) -> ChatInteraction:
        ...

    def get_history(self, username: str) -> list[ChatInteraction]:
        ...


class ChatAgentPort(Protocol):
    async def ask(self, *, username: str, role: str, message: str) -> str:
        ...

    async def healthcheck(self) -> dict[str, str]:
        ...
