from app.models import Treatment, Case
from app.core.constants import Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError
from app.repositories.base import get_scoped, flush_refresh
from .audit_service import audit


async def create(db, user, payload):
    require_role(user, Role.VETERINARIAN)
    case = await get_scoped(db, Case, payload.case_id, user, lock=True)
    if case.status not in ["UNDER_REVIEW", "CONFIRMED", "LAB_PENDING", "TREATMENT_ONGOING"]:
        raise DomainError("INVALID_TRANSITION", "Review the case before recording treatment.", 409)
    row = Treatment(
        **payload.model_dump(),
        animal_id=case.animal_id,
        veterinarian_id=user.id,
        owner_id=case.owner_id,
        district=case.district,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.flush()
    audit(db, user, "treatment_created", row)
    case.status = "TREATMENT_ONGOING"
    audit(db, user, "treatment_recorded", case, {"treatment_id": str(row.id)})
    return row


async def update(db, user, id, payload):
    require_role(user, Role.VETERINARIAN)
    row = await get_scoped(db, Treatment, id, user, lock=True)
    if payload.ended_on and payload.ended_on < row.started_on:
        raise DomainError("INVALID_DATES", "End date cannot precede start.", 422)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    audit(db, user, "treatment_updated", row)
    await flush_refresh(db, row)
    return row
