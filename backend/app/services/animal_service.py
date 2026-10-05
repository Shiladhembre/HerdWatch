from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from app.models import Animal, Herd, User, AnimalRecord
from app.core.constants import Role
from app.core.permissions import require_role, district_allowed
from app.core.exceptions import DomainError
from app.repositories.base import get_scoped, flush_refresh
from .audit_service import audit


def point(latitude, longitude):
    return (
        WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        if latitude is not None and longitude is not None
        else None
    )


async def owner_for(db, user, owner_id, district):
    district_allowed(user, district)
    owner_id = owner_id or user.id
    if user.role == Role.FARMER and owner_id != user.id:
        raise DomainError("OWNER_MISMATCH", "Farmers can manage only their own animals.", 403)
    owner = await db.get(User, owner_id)
    if not owner or not owner.is_active or owner.district != district:
        raise DomainError("INVALID_OWNER", "Owner must be active and belong to the record district.", 422)
    return owner_id


async def create(db, user, payload, model=Animal):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    values = payload.model_dump()
    values["owner_id"] = await owner_for(db, user, payload.owner_id, payload.district)
    row = model(**values, created_by=user.id, updated_by=user.id, geom=point(payload.latitude, payload.longitude))
    db.add(row)
    await db.flush()
    audit(db, user, "created", row)
    return row


async def update(db, user, id, payload, model=Animal):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    row = await get_scoped(db, model, id, user, lock=True)
    for key, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(row, key, value)
    row.updated_by = user.id
    audit(db, user, "updated", row)
    await flush_refresh(db, row)
    return row


async def subject(db, user, animal_id=None, herd_id=None):
    return await get_scoped(db, Animal if animal_id else Herd, animal_id or herd_id, user)


async def add_record(db, user, id, payload):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    await get_scoped(db, Animal, id, user)
    if payload.record_type == "Health record":
        require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN)
    row = AnimalRecord(animal_id=id, recorded_by=user.id, **payload.model_dump())
    db.add(row)
    await db.flush()
    audit(db, user, "health_record", row)
    return row


async def history(db, user, id):
    await get_scoped(db, Animal, id, user)
    return (
        await db.scalars(
            select(AnimalRecord).where(AnimalRecord.animal_id == id).order_by(AnimalRecord.created_at.desc()).limit(500)
        )
    ).all()
