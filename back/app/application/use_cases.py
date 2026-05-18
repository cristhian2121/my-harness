from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.exceptions import (
    AgentUnavailableError,
    UnsafePromptError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.entities import ChatInteraction, InteractionStatus, User
from app.domain.ports import ChatAgentPort, ChatRepository, UserRepository


@dataclass(slots=True)
class SecurityDecision:
    allowed: bool
    category: str | None = None
    reason: str | None = None


class InitUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, *, username: str, role: str) -> User:
        existing_user = self._user_repository.get_by_username(username)
        if existing_user is not None:
            raise UserAlreadyExistsError(f"User '{username}' already exists.")

        user = User(username=username, role=role)
        return self._user_repository.create(user)


class AskUseCase:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        chat_repository: ChatRepository,
        chat_agent: ChatAgentPort,
        validate_prompt: Callable[[str], SecurityDecision],
    ) -> None:
        self._user_repository = user_repository
        self._chat_repository = chat_repository
        self._chat_agent = chat_agent
        self._validate_prompt = validate_prompt

    async def execute(self, *, username: str, message: str) -> ChatInteraction:
        user = self._user_repository.get_by_username(username)
        if user is None:
            raise UserNotFoundError(f"User '{username}' was not found.")

        decision = self._validate_prompt(message)
        if not decision.allowed:
            blocked_response = (
                "No puedo ayudar con solicitudes que intenten vulnerar el sistema "
                "o evadir sus controles."
            )
            interaction = ChatInteraction(
                username=username,
                message=message,
                response=blocked_response,
                status=InteractionStatus.BLOCKED,
            )
            self._chat_repository.create(interaction)
            raise UnsafePromptError(blocked_response, decision.category or "blocked")

        try:
            response = await self._chat_agent.ask(
                username=username,
                role=user.role,
                message=message,
            )
        except AgentUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise AgentUnavailableError("The AI agent is currently unavailable.") from exc

        interaction = ChatInteraction(
            username=username,
            message=message,
            response=response,
            status=InteractionStatus.ANSWERED,
        )
        return self._chat_repository.create(interaction)


class GetHistoryUseCase:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self._user_repository = user_repository
        self._chat_repository = chat_repository

    def execute(self, *, username: str) -> list[ChatInteraction]:
        user = self._user_repository.get_by_username(username)
        if user is None:
            raise UserNotFoundError(f"User '{username}' was not found.")
        return self._chat_repository.get_history(username)


class HealthUseCase:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        chat_agent: ChatAgentPort,
    ) -> None:
        self._session_factory = session_factory
        self._chat_agent = chat_agent

    async def execute(self) -> dict[str, str]:
        database_status = "ok"
        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            database_status = "down"

        agent_status = await self._chat_agent.healthcheck()
        overall_status = "ok" if database_status == "ok" and agent_status["status"] == "ok" else "degraded"

        return {
            "status": overall_status,
            "database": database_status,
            "agent": agent_status["status"],
            "agent_detail": agent_status["detail"],
        }
