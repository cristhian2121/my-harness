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
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def ask(self, *, username: str, role: str, message: str) -> str:
        self.messages.append(message)
        if "Retrieved excerpts:" in message:
            question = next(
                (
                    line.removeprefix("User question: ").strip()
                    for line in message.splitlines()
                    if line.startswith("User question: ")
                ),
                message,
            )
            return f"Respuesta documental para {username} ({role}): {question}"
        return f"Respuesta para {username} ({role}): {message}"

    async def healthcheck(self) -> dict[str, str]:
        return {"status": "ok", "detail": "fake-agent"}


@pytest.fixture
def app_factory(tmp_path: Path):
    database_path = tmp_path / "test.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        google_api_key="test-key",
        document_storage_dir=str(tmp_path / "documents"),
        vector_store_dir=str(tmp_path / "vector-store"),
    )

    def _factory(*, chat_agent: FakeChatAgent | None = None, configure_container=None):
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
        container = build_container(
            settings=settings,
            chat_agent=chat_agent or FakeChatAgent(),
            engine=engine,
        )
        if configure_container is not None:
            configure_container(container)
        app = create_app(container=container)
        return TestClient(app)

    return _factory


@pytest.fixture
def client(app_factory) -> Generator[TestClient, None, None]:
    with app_factory() as test_client:
        yield test_client
