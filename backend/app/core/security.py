from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from pwdlib import PasswordHash
from app.config import get_settings
from app.core.exceptions import DomainError

password_hasher = PasswordHash.recommended()


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password, hashed):
    try:
        return password_hasher.verify(password, hashed)
    except Exception:
        return False


def create_token(user_id, session_id, kind="access"):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + (
        timedelta(minutes=settings.access_token_expire_minutes)
        if kind == "access"
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(uuid4()),
        "type": kind,
        "iat": now,
        "exp": expires,
        "iss": "herdwatch",
        "aud": "herdwatch-api",
    }
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm), payload


def decode_token(token, kind="access"):
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer="herdwatch",
            audience="herdwatch-api",
            options={"require": ["sub", "sid", "jti", "exp", "iat", "type"]},
        )
        if payload["type"] != kind:
            raise jwt.InvalidTokenError()
        from uuid import UUID

        UUID(payload["sub"])
        UUID(payload["sid"])
        UUID(payload["jti"])
        return payload
    except (jwt.PyJWTError, ValueError):
        raise DomainError("INVALID_TOKEN", "Invalid or expired authentication token.", 401) from None
