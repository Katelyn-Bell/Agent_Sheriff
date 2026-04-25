from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from agentsheriff.api.agents import router as agents_router
from agentsheriff.api.approvals import router as approvals_router
from agentsheriff.api.audit import router as audit_router
from agentsheriff.api.auth import router as auth_router
from agentsheriff.api.demo import router as demo_router
from agentsheriff.api.errors import install_error_handlers
from agentsheriff.api.evals import router as evals_router
from agentsheriff.api.health import router as health_router
from agentsheriff.api.openclaw import router as openclaw_router
from agentsheriff.api.policies import router as policies_router
from agentsheriff.api.skills import router as skills_router
from agentsheriff.api.tool_calls import router as tool_calls_router
from agentsheriff.api.tools import router as tools_router
from agentsheriff.config import Settings, get_settings
from agentsheriff.models.orm import Base, build_engine, build_session_factory
from agentsheriff.streams import router as stream_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    Base.metadata.create_all(engine)

    @asynccontextmanager
    async def lifespan(fapp: FastAPI) -> AsyncIterator[None]:
        # Telegram callback handling is delegated to the OpenClaw plugin
        # at demo/openclaw-config/plugins/agentsheriff-telegram-callbacks/
        # which forwards button taps to POST /v1/approvals/{id}.
        # We only send/edit messages here — no polling.
        if settings.telegram_bot_token and settings.telegram_chat_id:
            from agentsheriff.notifications import TelegramApprovalNotifier
            fapp.state.notifier = TelegramApprovalNotifier(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
            )
            logger.info("telegram_notifier_started chat_id=%s", settings.telegram_chat_id)

        yield

    app = FastAPI(title="AgentSheriff Gateway", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    install_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_s,
        same_site="lax",
        https_only=settings.cookie_secure,
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(openclaw_router)
    app.include_router(tool_calls_router)
    app.include_router(tools_router)
    app.include_router(skills_router)
    app.include_router(policies_router)
    app.include_router(audit_router)
    app.include_router(approvals_router)
    app.include_router(evals_router)
    app.include_router(agents_router)
    app.include_router(demo_router)
    app.include_router(stream_router)

    logger.info("agentsheriff_started")
    return app


app = create_app()


def get_db() -> Iterator[Session]:
    session_factory = app.state.session_factory
    with session_factory() as session:
        yield session


def get_app_settings() -> Settings:
    return app.state.settings
