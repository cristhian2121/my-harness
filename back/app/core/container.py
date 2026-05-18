from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.domain.ports import ChatAgentPort
from app.infrastructure.agent import AdkChatAgent, FallbackChatAgent
from app.infrastructure.db.models import Base
from app.infrastructure.security import PromptSecurityFilter


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    chat_agent: ChatAgentPort
    security_filter: PromptSecurityFilter

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)


def build_container(
    *,
    settings: Settings | None = None,
    chat_agent: ChatAgentPort | None = None,
    engine: Engine | None = None,
) -> AppContainer:
    resolved_settings = settings or get_settings()
    resolved_engine = engine or create_engine(
        resolved_settings.database_url,
        connect_args={"check_same_thread": False}
        if resolved_settings.database_url.startswith("sqlite")
        else {},
    )
    session_factory = sessionmaker(
        bind=resolved_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    resolved_chat_agent = chat_agent or (
        AdkChatAgent(resolved_settings)
        if resolved_settings.google_api_key
        else FallbackChatAgent("GOOGLE_API_KEY is not configured.")
    )

    return AppContainer(
        settings=resolved_settings,
        engine=resolved_engine,
        session_factory=session_factory,
        chat_agent=resolved_chat_agent,
        security_filter=PromptSecurityFilter(),
    )
