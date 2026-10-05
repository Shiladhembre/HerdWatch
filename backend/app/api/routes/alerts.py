from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.schemas.alert import AlertCreate
from app.schemas.analytics import Filters
from app.services import alert_service
from app.utils.responses import Envelope, ok
from app.utils.serialization import record

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await alert_service.list_alerts(db, user, filters))


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: AlertCreate, db: DB, user: CurrentUser):
    return ok(record(await alert_service.create(db, user, payload)))


@router.patch("/{id}/read", response_model=Envelope[dict])
async def mark_read(id: UUID, db: DB, user: CurrentUser):
    return ok(await alert_service.mark_read(db, user, id))
