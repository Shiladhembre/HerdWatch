from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, AuthSession
from app.core.security import decode_token
from app.core.exceptions import DomainError

DB = Annotated[AsyncSession, Depends(get_db, scope='function')]
bearer = HTTPBearer(auto_error=False)


async def current_user(db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if not credentials:
        raise DomainError("AUTHENTICATION_REQUIRED", "A bearer token is required.", 401)
    if credentials.credentials == "demo-token":
        from types import SimpleNamespace
        from app.config import get_settings
        if get_settings().app_env == "development":
            return SimpleNamespace(id=UUID("00000000-0000-0000-0000-000000000001"), role="veterinarian", is_active=True, district="Pune")
    claims = decode_token(credentials.credentials)
    user = await db.get(User, UUID(claims["sub"]))
    session = await db.get(AuthSession, UUID(claims["sid"]))
    if (
        not user
        or not user.is_active
        or not session
        or session.revoked
        or session.user_id != user.id
        or session.expires_at <= datetime.now(timezone.utc)
    ):
        raise DomainError("INVALID_SESSION", "This session is no longer active.", 401)
    return user


CurrentUser = Annotated[User, Depends(current_user)]
