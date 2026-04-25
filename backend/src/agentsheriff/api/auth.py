from __future__ import annotations

import uuid

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from agentsheriff.api.db import get_session
from agentsheriff.config import Settings, get_settings
from agentsheriff.models.dto import UserDTO
from agentsheriff.models.orm import User, utc_now

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_oauth: OAuth | None = None


def get_oauth() -> OAuth:
    global _oauth
    if _oauth is not None:
        return _oauth
    settings = get_settings()
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )
    _oauth = oauth
    return oauth


def current_user(
    request: Request,
    db: Session = Depends(get_session),
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="not_authenticated")
    user = db.get(User, user_id)
    if user is None:
        # session refers to a missing user — clear it so the client can re-login
        request.session.pop("user_id", None)
        raise HTTPException(status_code=401, detail="user_not_found")
    return user


def _user_to_dto(user: User) -> UserDTO:
    return UserDTO(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        onboarded=user.onboarded,
        created_at=user.created_at,
    )


def _post_login_redirect(
    settings: Settings, user: User
) -> str:
    target = "/onboard" if not user.onboarded else "/overview"
    return f"{settings.frontend_origin.rstrip('/')}{target}"


@router.get("/google/start")
async def google_start(request: Request) -> Response:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="oauth_not_configured",
        )
    oauth = get_oauth()
    return await oauth.google.authorize_redirect(
        request, settings.oauth_redirect_uri
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_session),
) -> Response:
    settings = get_settings()
    oauth = get_oauth()
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=400, detail=f"oauth_error: {exc.error}"
        )

    userinfo = token.get("userinfo")
    if userinfo is None:
        # fall back to the userinfo endpoint if id_token didn't carry claims
        userinfo = await oauth.google.userinfo(token=token)

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not sub or not email:
        raise HTTPException(status_code=400, detail="oauth_missing_claims")

    name = userinfo.get("name") or email
    avatar_url = userinfo.get("picture")

    user = db.query(User).filter(User.google_sub == sub).one_or_none()
    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            google_sub=sub,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)
    else:
        user.email = email
        user.name = name
        user.avatar_url = avatar_url
        user.last_login_at = utc_now()
    db.commit()

    request.session["user_id"] = user.id
    return RedirectResponse(
        url=_post_login_redirect(settings, user), status_code=302
    )


@router.get("/me", response_model=UserDTO)
def me(user: User = Depends(current_user)) -> UserDTO:
    return _user_to_dto(user)


@router.post("/logout", status_code=204)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=204)


@router.post("/me/onboarded", response_model=UserDTO)
def mark_onboarded(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> UserDTO:
    if not user.onboarded:
        user.onboarded = True
        db.commit()
        db.refresh(user)
    return _user_to_dto(user)
