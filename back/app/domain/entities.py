from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class InteractionStatus(StrEnum):
    ANSWERED = "answered"
    BLOCKED = "blocked"


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
