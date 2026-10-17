from __future__ import annotations

from datetime import datetime,timedelta,timezone

import bcrypt
import jwt


from hello_world.app.core.config import settings

ACCESS_TOKEN_COOKIE = "access_token"
JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(
        password_bytes, 
        bcrypt.gensalt(),
        )
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False

def create_access_token(
        user_id:str,
        username:str,
)->str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub":user_id,
        "username":username,
        "iat":now,
        "exp":now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token:str)->dict[str,object]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[JWT_ALGORITHM],
    )

