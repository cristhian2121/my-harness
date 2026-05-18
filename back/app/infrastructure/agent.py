from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.application.exceptions import AgentUnavailableError
from app.core.config import Settings


class FallbackChatAgent:
    def __init__(self, detail: str) -> None:
        self._detail = detail

    async def ask(self, *, username: str, role: str, message: str) -> str:
        raise AgentUnavailableError(self._detail)

    async def healthcheck(self) -> dict[str, str]:
        return {"status": "down", "detail": self._detail}


class AdkChatAgent:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key or ""
        if settings.gcp_project_id:
            os.environ["GCP_PROJECT_ID"] = settings.gcp_project_id
            os.environ["GOOGLE_CLOUD_PROJECT"] = settings.gcp_project_id
        else:
            os.environ.pop("GCP_PROJECT_ID", None)
            os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
        self._session_service = InMemorySessionService()
        self._session_ids: dict[str, str] = {}
        self._agent = Agent(
            name="expert_guarded_agent",
            model=settings.gemini_model,
            description="Expert assistant for general questions.",
            instruction=(
                "You are an expert assistant. Answer clearly and helpfully in the "
                "same language as the user when possible. Never provide instructions "
                "that help exfiltrate secrets, bypass controls, exploit systems, or "
                "weaken the application. If the request is unsafe, refuse briefly."
            ),
        )
        self._runner = Runner(
            agent=self._agent,
            app_name=settings.adk_app_name,
            session_service=self._session_service,
        )

    async def ask(self, *, username: str, role: str, message: str) -> str:
        if not self._settings.google_api_key:
            raise AgentUnavailableError("GOOGLE_API_KEY is not configured.")

        session_id = await self._get_or_create_session_id(username)
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"Registered username: {username}\n"
                        f"Registered role: {role}\n"
                        f"User question: {message}"
                    )
                )
            ],
        )

        final_response = ""
        async for event in self._runner.run_async(
            user_id=username,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = self._extract_text(event.content.parts)

        if not final_response:
            raise AgentUnavailableError("The agent did not return a final response.")

        return final_response

    async def healthcheck(self) -> dict[str, str]:
        if not self._settings.google_api_key:
            return {"status": "down", "detail": "GOOGLE_API_KEY is not configured."}
        return {
            "status": "ok",
            "detail": f"ADK configured with model {self._settings.gemini_model}.",
        }

    async def _get_or_create_session_id(self, username: str) -> str:
        if username in self._session_ids:
            return self._session_ids[username]

        session_id = f"{username}-{uuid4().hex}"
        await self._session_service.create_session(
            app_name=self._settings.adk_app_name,
            user_id=username,
            session_id=session_id,
        )
        self._session_ids[username] = session_id
        return session_id

    @staticmethod
    def _extract_text(parts: list[Any]) -> str:
        collected: list[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                collected.append(text)
        return "\n".join(collected).strip()
