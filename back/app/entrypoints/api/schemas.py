from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InitUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    role: str = Field(min_length=2, max_length=100)


class UserResponse(BaseModel):
    username: str
    role: str
    created_at: datetime | None = None


class InitUserResponse(BaseModel):
    message: str
    user: UserResponse


class ValidateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    role: str = Field(min_length=2, max_length=100)


class ValidateUserResponse(BaseModel):
    message: str
    user: UserResponse


class AskRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    message: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    username: str
    message: str
    response: str
    status: Literal["answered", "blocked"]
    created_at: datetime | None = None


class HistoryItemResponse(BaseModel):
    message: str
    response: str
    status: Literal["answered", "blocked"]
    created_at: datetime | None = None


class HistoryResponse(BaseModel):
    username: str
    items: list[HistoryItemResponse]


class DocumentResponse(BaseModel):
    id: str
    username: str
    filename: str
    content_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    status: Literal["uploaded", "indexed", "failed"]
    chunk_count: int
    page_count: int | None = None
    row_count: int | None = None
    sheet_names: list[str] | None = None
    error_detail: str | None = None
    created_at: datetime | None = None


class DocumentListResponse(BaseModel):
    username: str
    items: list[DocumentResponse]


class DocumentQuestionRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    question: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] = Field(min_length=1)


class DocumentSourceResponse(BaseModel):
    chunk_id: int
    document_id: str
    filename: str
    snippet: str
    score: float
    chunk_index: int
    page_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None


class DocumentQuestionResponse(BaseModel):
    username: str
    question: str
    answer: str
    status: Literal["answered", "blocked"]
    document_ids: list[str]
    sources: list[DocumentSourceResponse]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: str
    agent: str
    agent_detail: str


class ErrorResponse(BaseModel):
    detail: str
