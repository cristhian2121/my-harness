from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class InteractionStatus(StrEnum):
    ANSWERED = "answered"
    BLOCKED = "blocked"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    FAILED = "failed"


@dataclass(slots=True)
class User:
    username: str
    role: str
    created_at: datetime | None = None


@dataclass(slots=True)
class ChatInteraction:
    username: str
    message: str
    response: str
    status: InteractionStatus
    created_at: datetime | None = None


@dataclass(slots=True)
class Document:
    id: str
    username: str
    filename: str
    content_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    storage_path: str
    status: DocumentStatus
    chunk_count: int = 0
    page_count: int | None = None
    row_count: int | None = None
    sheet_names: list[str] | None = None
    error_detail: str | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class DocumentChunk:
    id: int | None
    document_id: str
    chunk_index: int
    text: str
    page_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ParsedDocument:
    chunks: list[DocumentChunk]
    page_count: int | None = None
    row_count: int | None = None
    sheet_names: list[str] | None = None


@dataclass(slots=True)
class RetrievedDocumentChunk:
    chunk_id: int
    document_id: str
    filename: str
    text: str
    score: float
    chunk_index: int
    page_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None


@dataclass(slots=True)
class DocumentAnswer:
    username: str
    question: str
    answer: str
    status: InteractionStatus
    document_ids: list[str]
    sources: list[RetrievedDocumentChunk]
