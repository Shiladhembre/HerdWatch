from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import select, or_
from app.models import User, AuthSession
from app.core.constants import Role
from app.core.security import hash_password, verify_password, create_token, decode_token
from app.core.exceptions import DomainError
from app.schemas.user import UserView

DUMMY_HASH = hash_password("not-a-valid-user-password-for-timing-only")


async def register(db, payload):
    if payload.role != Role.FARMER:
        raise DomainError(
            "STAFF_APPROVAL_REQUIRED", "Staff accounts must be created or promoted by an administrator.", 403
        )
    exists = await db.scalar(select(User.id).where(or_(User.email == payload.email, User.mobile == payload.mobile)))
    if exists:
        raise DomainError("ACCOUNT_CONFLICT", "An account with these credentials already exists.", 409)
    values = payload.model_dump(exclude={"password"})
    user = User(**values, password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()
    return UserView.model_validate(user)


async def token_pair(db, user, session=None):
    sid = session.id if session else uuid4()
    access, _ = create_token(user.id, sid)
    refresh, claims = create_token(user.id, sid, "refresh")
    if session:
        session.refresh_jti = claims["jti"]
        session.expires_at = claims["exp"]
    else:
        db.add(AuthSession(id=sid, user_id=user.id, refresh_jti=claims["jti"], expires_at=claims["exp"]))
    await db.flush()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": UserView.model_validate(user),
    }


async def login(db, payload):
    identifier = payload.identifier.lower()
    user = await db.scalar(select(User).where(or_(User.email == identifier, User.mobile == identifier)))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise DomainError("INVALID_CREDENTIALS", "Invalid credentials or inactive account.", 401)
    return await token_pair(db, user)


async def refresh(db, token):
    claims = decode_token(token, "refresh")
    session = await db.scalar(select(AuthSession).where(AuthSession.id == UUID(claims["sid"])).with_for_update())
    if (
        not session
        or session.revoked
        or session.refresh_jti != claims["jti"]
        or session.expires_at <= datetime.now(timezone.utc)
    ):
        raise DomainError("INVALID_REFRESH_TOKEN", "Refresh token is expired, revoked or already used.", 401)
    user = await db.get(User, session.user_id)
    if not user or not user.is_active or str(user.id) != claims["sub"]:
        raise DomainError("INVALID_SESSION", "Account is inactive.", 401)
    return await token_pair(db, user, session)


async def logout(db, user, token):
    claims = decode_token(token, "refresh")
    if claims["sub"] != str(user.id):
        raise DomainError("INVALID_TOKEN", "Token does not belong to the current user.", 401)
    session = await db.get(AuthSession, UUID(claims["sid"]))
    if session:
        session.revoked = True
