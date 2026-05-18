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


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: str
    agent: str
    agent_detail: str


class ErrorResponse(BaseModel):
    detail: str
