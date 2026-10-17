from __future__ import annotations

import jwt
from fastapi import HTTPException, Request, status

from hello_world.app.core.security import (
    ACCESS_TOKEN_COOKIE,
    decode_access_token,
)
from hello_world.app.services.users import get_user_by_id


def get_current_user(
    request: Request,
) -> dict[str, str]:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    authorization = request.headers.get("Authorization", "")

    if not token and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录。",
        )

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录。",
        ) from exc

    user_id = payload.get("sub")

    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证。",
        )

    user = get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在。",
        )

    return user