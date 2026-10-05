from uuid import UUID
from fastapi import APIRouter
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models import User
from app.schemas.user import UserView, ProfileUpdate, AdminUserUpdate
from app.core.constants import Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError
from app.services.audit_service import audit
from app.utils.responses import Envelope, ok

router = APIRouter(prefix="/users", tags=["Users"])


@router.patch("/me", response_model=Envelope[UserView])
async def profile(payload: ProfileUpdate, db: DB, user: CurrentUser):
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(user, k, v)
    audit(db, user, "profile_updated", user)
    await db.flush()
    return ok(UserView.model_validate(user))


@router.get("/veterinarians", response_model=Envelope[list[dict]])
async def veterinarians(db: DB, user: CurrentUser):
    rows = (
        await db.execute(
            select(User.id, User.full_name, User.district)
            .where(
                User.role == Role.VETERINARIAN,
                User.is_active.is_(True),
                True if user.role == Role.ADMIN else User.district == user.district,
            )
            .limit(100)
        )
    ).mappings()
    return ok([dict(r) for r in rows])


@router.patch("/{id}", response_model=Envelope[UserView])
async def admin_update(id: UUID, payload: AdminUserUpdate, db: DB, user: CurrentUser):
    require_role(user, Role.ADMIN)
    target = await db.get(User, id)
    if not target:
        raise DomainError("USER_NOT_FOUND", "User not found.", 404)
    if id == user.id and (payload.is_active is False or payload.role and payload.role != Role.ADMIN):
        raise DomainError("SELF_DEMOTION", "Use another administrator to change your own administrative access.", 409)
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(target, k, v)
    audit(db, user, "admin_user_updated", target, {"fields": list(payload.model_fields_set)})
    await db.flush()
    return ok(UserView.model_validate(target))
