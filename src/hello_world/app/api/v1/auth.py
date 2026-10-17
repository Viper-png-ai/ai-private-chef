from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from hello_world.app.api.dependencies import get_current_user
from hello_world.app.core.config import settings
from hello_world.app.core.security import (
    ACCESS_TOKEN_COOKIE,
    create_access_token,
)
from hello_world.app.models.schemas import (
    AuthRequest,
    SuccessResponse,
    UserResponse,
)
from hello_world.app.services.users import (
    authenticate_user,
    create_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(
    response: Response,
    token: str,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _public_user(
    user: dict[str, str],
) -> UserResponse:
    return UserResponse(
        id=user["id"],
        username=user["username"],
        created_at=user["created_at"],
    )

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: AuthRequest,
    response: Response,
) -> UserResponse:
    user = create_user(
        payload.username,
        payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=409,
            detail="用户名已存在。",
        )

    token = create_access_token(
        user["id"],
        user["username"],
    )
    _set_auth_cookie(response, token)

    return _public_user(user)


@router.post(
    "/login",
    response_model=UserResponse,
)
def login(
    payload: AuthRequest,
    response: Response,
) -> UserResponse:
    user = authenticate_user(
        payload.username,
        payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误。",
        )

    token = create_access_token(
        user["id"],
        user["username"],
    )
    _set_auth_cookie(response, token)

    return _public_user(user)


@router.post(
    "/logout",
    response_model=SuccessResponse,
)
def logout(response: Response) -> SuccessResponse:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
    )
    return SuccessResponse(success=True)


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    user: dict[str, str] = Depends(get_current_user),
) -> UserResponse:
    return _public_user(user)