from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.domain.ports import (
    ChatAgentPort,
    DocumentParserPort,
    DocumentStoragePort,
    EmbeddingPort,
    VectorStorePort,
)
from app.infrastructure.agent import AdkChatAgent, FallbackChatAgent
from app.infrastructure.db.models import Base
from app.infrastructure.documents import (
    LocalDocumentParser,
    LocalDocumentStorage,
    LocalHashEmbeddingService,
    LocalQdrantVectorStore,
)
from app.infrastructure.security import PromptSecurityFilter


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    chat_agent: ChatAgentPort
    security_filter: PromptSecurityFilter
    document_storage: DocumentStoragePort
    document_parser: DocumentParserPort
    embedding_service: EmbeddingPort
    vector_store: VectorStorePort

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        close_vector_store = getattr(self.vector_store, "close", None)
        if callable(close_vector_store):
            close_vector_store()
        self.engine.dispose()


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
    document_storage = LocalDocumentStorage(Path(resolved_settings.document_storage_dir))
    document_parser = LocalDocumentParser()
    embedding_service = LocalHashEmbeddingService(resolved_settings.embedding_dimensions)
    vector_store = LocalQdrantVectorStore(
        root_directory=Path(resolved_settings.vector_store_dir),
    )

    return AppContainer(
        settings=resolved_settings,
        engine=resolved_engine,
        session_factory=session_factory,
        chat_agent=resolved_chat_agent,
        security_filter=PromptSecurityFilter(),
        document_storage=document_storage,
        document_parser=document_parser,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )
