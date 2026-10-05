from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.models import Case
from app.schemas.analytics import Filters
from app.services import analytics_service
from app.repositories.base import filtered
from app.utils.responses import Envelope, ok
from app.utils.serialization import record

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=Envelope[dict])
async def dashboard(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await analytics_service.dashboard(db, user, filters))


@router.get("/disease-trends", response_model=Envelope[list[dict]])
async def trends(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await analytics_service.trends(db, user, filters))


@router.get("/mortality", response_model=Envelope[list[dict]])
async def mortality(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await analytics_service.trends(db, user, filters))


@router.get("/species", response_model=Envelope[list[dict]])
async def species(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await analytics_service.grouped(db, user, filters, "species"))


@router.get("/risk-distribution", response_model=Envelope[list[dict]])
async def risk(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await analytics_service.grouped(db, user, filters, "risk"))


@router.get("/vaccination-coverage", response_model=Envelope[dict])
async def coverage(db: DB, user: CurrentUser):
    return ok(await analytics_service.coverage(db, user))


@router.get("/export", response_model=Envelope[list[dict]])
async def export(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    """Up to 10,000 scoped case rows for client-side CSV export; split larger exports by date."""
    rows = (await db.scalars(filtered(Case, user, filters).order_by(Case.created_at.desc()).limit(10000))).all()
    return ok(
        [
            record(r, exclude=["owner_id", "reporter_id", "clinical_assessment", "notes", "observed_symptoms"])
            for r in rows
        ]
    )
