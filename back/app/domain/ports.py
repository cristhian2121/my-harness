from __future__ import annotations

from typing import Protocol

from app.domain.entities import (
    ChatInteraction,
    Document,
    DocumentChunk,
    ParsedDocument,
    RetrievedDocumentChunk,
    User,
)


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


class DocumentRepository(Protocol):
    def create(self, document: Document) -> Document:
        ...

    def update(self, document: Document) -> Document:
        ...

    def list_by_username(self, username: str) -> list[Document]:
        ...

    def get_by_id(self, document_id: str) -> Document | None:
        ...


class DocumentChunkRepository(Protocol):
    def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        ...


class DocumentStoragePort(Protocol):
    def store(self, *, document_id: str, filename: str, content: bytes) -> str:
        ...


class DocumentParserPort(Protocol):
    def parse(self, *, filename: str, content: bytes) -> ParsedDocument:
        ...


class EmbeddingPort(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class VectorStorePort(Protocol):
    def index_chunks(
        self,
        *,
        username: str,
        document: Document,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
    ) -> None:
        ...

    def search(
        self,
        *,
        username: str,
        vector: list[float],
        document_ids: list[str],
        limit: int,
    ) -> list[RetrievedDocumentChunk]:
        ...
