from __future__ import annotations

import logging
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from agentsheriff.api.health import router as health_router
from agentsheriff.config import Settings, get_settings
from agentsheriff.models.orm import Base, build_engine, build_session_factory

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    Base.metadata.create_all(engine)

    app = FastAPI(title="AgentSheriff Gateway", version="0.1.0")
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)

    logger.info("agentsheriff_started")
    return app


app = create_app()


def get_db() -> Iterator[Session]:
    session_factory = app.state.session_factory
    with session_factory() as session:
        yield session


def get_app_settings() -> Settings:
    return app.state.settings
