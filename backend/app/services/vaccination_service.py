from app.models import Vaccination
from app.core.constants import Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError
from app.repositories.base import get_scoped, flush_refresh
from .animal_service import subject
from .audit_service import audit


async def create(db, user, payload):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN)
    animal = await subject(db, user, payload.animal_id, payload.herd_id)
    row = Vaccination(
        **payload.model_dump(),
        owner_id=animal.owner_id,
        district=animal.district,
        village=animal.village,
        administered_by=user.id,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.flush()
    audit(db, user, "vaccination_created", row)
    return row


async def update(db, user, id, payload):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN)
    row = await get_scoped(db, Vaccination, id, user, lock=True)
    if payload.next_due_on and payload.next_due_on < row.administered_on:
        raise DomainError("INVALID_DATES", "Due date cannot precede administration.", 422)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_by = user.id
    audit(db, user, "vaccination_updated", row)
    await flush_refresh(db, row)
    return row
