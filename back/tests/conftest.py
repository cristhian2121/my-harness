from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.core.config import Settings
from app.core.container import build_container
from app.main import create_app


class FakeChatAgent:
    async def ask(self, *, username: str, role: str, message: str) -> str:
        return f"Respuesta para {username} ({role}): {message}"

    async def healthcheck(self) -> dict[str, str]:
        return {"status": "ok", "detail": "fake-agent"}


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "test.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        google_api_key="test-key",
    )
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    container = build_container(
        settings=settings,
        chat_agent=FakeChatAgent(),
        engine=engine,
    )
    app = create_app(container=container)

    with TestClient(app) as test_client:
        yield test_client
