from uuid import uuid4
from app.models import LabReferral, Case, Alert
from app.core.constants import Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError, DuplicateSubmission
from app.repositories.base import get_scoped, flush_refresh
from .audit_service import audit

LAB_TRANSITIONS = {
    "REQUESTED": {"COLLECTED"},
    "COLLECTED": {"IN_TRANSIT", "RECEIVED"},
    "IN_TRANSIT": {"RECEIVED"},
    "RECEIVED": {"TESTING"},
    "TESTING": set(),
    "RESULT_AVAILABLE": {"CLOSED"},
    "CLOSED": set(),
}


async def create(db, user, payload):
    require_role(user, Role.VETERINARIAN)
    case = await get_scoped(db, Case, payload.case_id, user, lock=True)
    if case.status in ("CLOSED", "RESOLVED"):
        raise DomainError("CASE_CLOSED", "Reopen the case before requesting a sample.", 409)
    row = LabReferral(
        **payload.model_dump(),
        sample_reference=f"LAB-{uuid4().hex[:12].upper()}",
        animal_id=case.animal_id,
        owner_id=case.owner_id,
        district=case.district,
        requested_by=user.id,
        suspected_disease=case.suspected_disease,
        created_by=user.id,
        updated_by=user.id,
        status="COLLECTED" if payload.collection_date else "REQUESTED",
    )
    db.add(row)
    await db.flush()
    case.status = "SAMPLE_REQUESTED"
    audit(db, user, "referral_created", row)
    audit(db, user, "sample_requested", case, {"sample_reference": row.sample_reference})
    return row


async def update(db, user, id, payload):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN)
    row = await get_scoped(db, LabReferral, id, user, lock=True)
    if payload.status != row.status and payload.status not in LAB_TRANSITIONS[row.status]:
        raise DomainError(
            "INVALID_LAB_TRANSITION",
            f"Cannot move from {row.status} to {payload.status}. Results use the authorised result endpoint.",
            409,
        )
    if payload.status == "COLLECTED" and not (payload.collection_date or row.collection_date):
        raise DomainError("COLLECTION_DATE_REQUIRED", "Record a collection date.", 422)
    for key, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(row, key, value)
    case = await get_scoped(db, Case, row.case_id, user, lock=True)
    if row.status in ("IN_TRANSIT", "RECEIVED", "TESTING") and case.status not in ("CLOSED", "RESOLVED"):
        case.status = "LAB_PENDING"
    audit(db, user, "sample_status_updated", row, {"status": row.status})
    audit(db, user, "laboratory_update", case, {"status": row.status})
    await flush_refresh(db, row)
    return row


async def result(db, user, id, payload, key):
    require_role(user, Role.VETERINARIAN)
    row = await get_scoped(db, LabReferral, id, user, lock=True)
    if row.result is not None:
        if row.result_key == key and row.result == payload.result and row.result_date == payload.result_date:
            return row
        raise DuplicateSubmission()
    if row.status != "TESTING":
        raise DomainError("INVALID_LAB_TRANSITION", "Only a sample in testing can receive a result.", 409)
    if row.collection_date and payload.result_date < row.collection_date:
        raise DomainError("INVALID_DATES", "Result date cannot precede collection.", 422)
    row.result = payload.result
    row.result_date = payload.result_date
    row.result_key = key
    row.status = "RESULT_AVAILABLE"
    case = await get_scoped(db, Case, row.case_id, user, lock=True)
    if case.status == "LAB_PENDING":
        case.status = "UNDER_REVIEW"
    audit(db, user, "lab_result_submitted", row)
    audit(db, user, "lab_result_available", case, {"sample_reference": row.sample_reference})
    db.add(
        Alert(
            type="LAB_RESULT",
            severity="INFO",
            title="Laboratory result available",
            message=f"Veterinary review is required for case {case.case_reference}.",
            district=row.district,
            user_id=case.owner_id,
            case_id=case.id,
            created_by=user.id,
        )
    )
    await flush_refresh(db, row)
    return row
