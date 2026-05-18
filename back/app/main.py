from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.core.container import AppContainer, build_container
from app.entrypoints.api.routes import router


def create_app(container: AppContainer | None = None, settings: Settings | None = None) -> FastAPI:
    resolved_container = container or build_container(settings=settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        resolved_container.create_schema()
        app.state.container = resolved_container
        try:
            yield
        finally:
            resolved_container.close()

    app = FastAPI(
        title=resolved_container.settings.app_name,
        description=resolved_container.settings.app_description,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_container.settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=resolved_container.settings.api_prefix)
    return app


app = create_app()
