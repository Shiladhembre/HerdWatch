from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.config import get_settings
from app.dependencies import DB, CurrentUser
from app.models import Case, Attachment, CaseSymptom, Prediction
from app.schemas.case import CaseCreate, CaseUpdate, AssignInput, SyncInput
from app.schemas.common import NoteInput
from app.schemas.analytics import Filters
from app.services import case_service, upload_service
from app.repositories.base import filtered, paginate, get_scoped
from app.core.exceptions import DomainError
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(tags=["Cases"])


@router.get("/cases", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    order = Case.created_at.desc() if filters.sort == "newest" else Case.created_at.asc()
    return ok(page(await paginate(db, filtered(Case, user, filters).order_by(order), filters)))


@router.post("/cases", response_model=Envelope[dict], status_code=201)
async def create(
    payload: CaseCreate,
    db: DB,
    user: CurrentUser,
    idempotency_key: Annotated[str | None, Header(max_length=100)] = None,
):
    row, duplicate = await case_service.create(db, user, payload, idempotency_key)
    return ok({**record(row), "duplicate": duplicate}, "Existing report returned" if duplicate else "Case created")


@router.get("/cases/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    row = await get_scoped(db, Case, id, user)
    timeline = await case_service.timeline(db, user, id)
    symptoms = (await db.scalars(select(CaseSymptom).where(CaseSymptom.case_id == id))).all()
    predictions = (
        await db.scalars(
            select(Prediction).where(Prediction.case_id == id).order_by(Prediction.created_at.desc()).limit(50)
        )
    ).all()
    return ok(
        {
            **record(row),
            "timeline": [record(r) for r in timeline],
            "symptoms": {s.symptom_code: s.symptom_value for s in symptoms},
            "predictions": [record(p) for p in predictions],
        }
    )


@router.patch("/cases/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: CaseUpdate, db: DB, user: CurrentUser):
    return ok(record(await case_service.update(db, user, id, payload)))


@router.post("/cases/{id}/assign", response_model=Envelope[dict])
async def assign(id: UUID, payload: AssignInput, db: DB, user: CurrentUser):
    return ok(record(await case_service.assign(db, user, id, payload.veterinarian_id)))


@router.post("/cases/{id}/escalate", response_model=Envelope[dict])
async def escalate(id: UUID, payload: NoteInput, db: DB, user: CurrentUser):
    return ok(record(await case_service.escalate(db, user, id, payload.notes)))


@router.post("/cases/{id}/assistance", response_model=Envelope[dict])
async def assistance(id: UUID, payload: NoteInput, db: DB, user: CurrentUser):
    return ok(record(await case_service.escalate(db, user, id, payload.notes, True)))


@router.post("/cases/{id}/close", response_model=Envelope[dict])
async def close(id: UUID, payload: NoteInput, db: DB, user: CurrentUser):
    return ok(record(await case_service.update(db, user, id, CaseUpdate(status="CLOSED", notes=payload.notes))))


@router.post("/cases/{id}/attachments", response_model=Envelope[dict], status_code=201)
async def attachment(id: UUID, db: DB, user: CurrentUser, file: Annotated[UploadFile, File()]):
    return ok(record(await upload_service.upload(db, user, id, file)))


@router.get("/cases/{id}/attachments", response_model=Envelope[list[dict]])
async def attachments(id: UUID, db: DB, user: CurrentUser):
    await get_scoped(db, Case, id, user)
    return ok(
        [record(r) for r in (await db.scalars(select(Attachment).where(Attachment.case_id == id).limit(100))).all()]
    )


@router.get("/cases/{id}/attachments/{attachment_id}")
async def download(id: UUID, attachment_id: UUID, db: DB, user: CurrentUser):
    await get_scoped(db, Case, id, user)
    row = await db.get(Attachment, attachment_id)
    if not row or row.case_id != id:
        raise DomainError("NOT_FOUND", "Attachment not found.", 404)
    root = get_settings().upload_dir.resolve()
    path = (root / row.storage_key).resolve()
    if path.parent != root or not path.is_file():
        raise DomainError("NOT_FOUND", "Attachment unavailable.", 404)
    return FileResponse(
        path,
        media_type=row.content_type,
        filename=f"attachment-{row.id}{path.suffix}",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/sync", response_model=Envelope[list[dict]])
async def sync(payload: SyncInput, db: DB, user: CurrentUser):
    results = []
    for item in payload.records:
        try:
            async with db.begin_nested():
                values = item.payload.model_copy(update={"created_offline_at": item.created_offline_at})
                values = CaseCreate.model_validate(values.model_dump())
                row, duplicate = await case_service.create(db, user, values, item.client_record_id)
                await db.flush()
            results.append(
                {
                    "client_record_id": item.client_record_id,
                    "status": "duplicate" if duplicate else "synced",
                    "case_id": row.id,
                }
            )
        except DomainError as e:
            results.append(
                {
                    "client_record_id": item.client_record_id,
                    "status": "failed",
                    "error": {"code": e.code, "message": e.message},
                }
            )
    return ok(results)
