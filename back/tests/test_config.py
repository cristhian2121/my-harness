from __future__ import annotations

from app.core.config import Settings
from app.infrastructure.agent import AdkChatAgent


def test_settings_read_requested_env_names(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "env-test-key")
    monkeypatch.setenv("GCP_PROJECT_ID", "env-project")
    monkeypatch.setenv("WALT_MODEL", "gemini-env-model")

    settings = Settings()

    assert settings.google_api_key == "env-test-key"
    assert settings.gcp_project_id == "env-project"
    assert settings.gemini_model == "gemini-env-model"


def test_adk_agent_propagates_project_id_to_runtime(monkeypatch):
    class FakeSessionService:
        async def create_session(self, *, app_name, user_id, session_id):
            return None

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeRunner:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr("app.infrastructure.agent.InMemorySessionService", FakeSessionService)
    monkeypatch.setattr("app.infrastructure.agent.Agent", FakeAgent)
    monkeypatch.setattr("app.infrastructure.agent.Runner", FakeRunner)

    settings = Settings(
        google_api_key="runtime-key",
        gcp_project_id="runtime-project",
        gemini_model="runtime-model",
    )
    agent = AdkChatAgent(settings)

    assert agent._agent.kwargs["model"] == "runtime-model"
    assert agent._runner.kwargs["app_name"] == settings.adk_app_name
    assert agent._runner.kwargs["session_service"] is agent._session_service
    assert agent._runner.kwargs["agent"] is agent._agent
    assert agent._session_service.__class__ is FakeSessionService
    assert agent._session_ids == {}
    assert __import__("os").environ["GOOGLE_API_KEY"] == "runtime-key"
    assert __import__("os").environ["GCP_PROJECT_ID"] == "runtime-project"
    assert __import__("os").environ["GOOGLE_CLOUD_PROJECT"] == "runtime-project"
