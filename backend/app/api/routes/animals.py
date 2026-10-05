from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models import Animal, Vaccination, Case, Treatment, LabReferral
from app.schemas.animal import AnimalCreate, AnimalUpdate, AnimalRecordInput
from app.schemas.analytics import Filters
from app.services import animal_service
from app.services.audit_service import audit
from app.repositories.base import filtered, paginate, get_scoped
from app.core.constants import Role
from app.core.permissions import require_role
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/animals", tags=["Animals"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    stmt = filtered(Animal, user, filters).order_by(Animal.created_at.desc())
    return ok(page(await paginate(db, stmt, filters)))


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: AnimalCreate, db: DB, user: CurrentUser):
    return ok(record(await animal_service.create(db, user, payload)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    return ok(record(await get_scoped(db, Animal, id, user)))


@router.patch("/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: AnimalUpdate, db: DB, user: CurrentUser):
    return ok(record(await animal_service.update(db, user, id, payload)))


@router.delete("/{id}", response_model=Envelope[dict])
async def delete(id: UUID, db: DB, user: CurrentUser):
    require_role(user, Role.FARMER, Role.VETERINARIAN)
    row = await get_scoped(db, Animal, id, user)
    audit(db, user, "animal_deleted", row)
    await db.delete(row)
    await db.flush()
    return ok({"deleted": True})


@router.get("/{id}/history", response_model=Envelope[dict])
async def history(id: UUID, db: DB, user: CurrentUser):
    history = await animal_service.history(db, user, id)
    result = {"records": [record(r) for r in history]}
    for name, model in [
        ("vaccinations", Vaccination),
        ("cases", Case),
        ("treatments", Treatment),
        ("laboratory", LabReferral),
    ]:
        result[name] = [
            record(r)
            for r in (
                await db.scalars(
                    select(model).where(model.animal_id == id).order_by(model.created_at.desc()).limit(500)
                )
            ).all()
        ]
    return ok(result)


@router.get("/{id}/vaccinations", response_model=Envelope[list[dict]])
async def vaccinations(id: UUID, db: DB, user: CurrentUser):
    await get_scoped(db, Animal, id, user)
    return ok(
        [
            record(r)
            for r in (
                await db.scalars(
                    select(Vaccination)
                    .where(Vaccination.animal_id == id)
                    .order_by(Vaccination.created_at.desc())
                    .limit(500)
                )
            ).all()
        ]
    )


@router.post("/{id}/records", response_model=Envelope[dict], status_code=201)
async def add_record(id: UUID, payload: AnimalRecordInput, db: DB, user: CurrentUser):
    return ok(record(await animal_service.add_record(db, user, id, payload)))
