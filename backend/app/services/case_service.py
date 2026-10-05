import hashlib
import json
from uuid import uuid4
from sqlalchemy import select, text
from app.models import Case, CaseSymptom, User, Alert, AuditLog
from app.core.constants import Role
from app.core.permissions import require_role, district_allowed
from app.core.exceptions import DomainError, DuplicateSubmission
from app.repositories.base import get_scoped, flush_refresh
from .animal_service import subject, point
from .audit_service import audit

TRANSITIONS = {
    "REPORTED": {"UNDER_REVIEW", "SAMPLE_REQUESTED"},
    "UNDER_REVIEW": {"SAMPLE_REQUESTED", "CONFIRMED", "TREATMENT_ONGOING", "RESOLVED"},
    "SAMPLE_REQUESTED": {"LAB_PENDING", "UNDER_REVIEW"},
    "LAB_PENDING": {"UNDER_REVIEW", "CONFIRMED", "TREATMENT_ONGOING", "RESOLVED"},
    "CONFIRMED": {"TREATMENT_ONGOING", "RESOLVED"},
    "TREATMENT_ONGOING": {"SAMPLE_REQUESTED", "RESOLVED"},
    "RESOLVED": {"CLOSED", "UNDER_REVIEW"},
    "CLOSED": set(),
}


async def create(db, user, payload, key=None):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    district_allowed(user, payload.district)
    request_hash = hashlib.sha256(json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    if key:
        if len(key) > 100 or len(key) < 8:
            raise DomainError("INVALID_IDEMPOTENCY_KEY", "Idempotency key must be 8–100 characters.", 422)
        lock = int.from_bytes(hashlib.sha256(f"{user.id}:{key}".encode()).digest()[:8], signed=True)
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
        existing = await db.scalar(select(Case).where(Case.reporter_id == user.id, Case.client_record_id == key))
        if existing:
            if existing.request_hash != request_hash:
                raise DuplicateSubmission()
            return existing, True
    animal = await subject(db, user, payload.animal_id, payload.herd_id)
    if animal.district != payload.district or animal.species != payload.species:
        raise DomainError("SUBJECT_MISMATCH", "Subject species and district must match the case.", 422)
    if payload.herd_id and payload.affected_count > animal.animal_count:
        raise DomainError("COUNT_EXCEEDS_HERD", "Affected count exceeds the registered herd size.", 422)
    if payload.animal_id and payload.affected_count != 1:
        raise DomainError(
            "INDIVIDUAL_COUNT",
            "An individual animal case must have affected_count=1; use a herd for multiple animals.",
            422,
        )
    risk = (
        "HIGH" if payload.severity in ("URGENT", "CRITICAL") else "MEDIUM" if payload.severity == "MODERATE" else "LOW"
    )
    row = Case(
        **payload.model_dump(exclude={"symptoms"}),
        case_reference=f"HW-{uuid4().hex[:12].upper()}",
        reporter_id=user.id,
        owner_id=animal.owner_id,
        client_record_id=key,
        request_hash=request_hash,
        risk_level=risk,
        created_by=user.id,
        updated_by=user.id,
        geom=point(payload.latitude, payload.longitude),
    )
    db.add(row)
    await db.flush()
    for code, value in payload.symptoms.items():
        db.add(CaseSymptom(case_id=row.id, symptom_code=code, symptom_value=value))
    audit(db, user, "reported", row, {"status": row.status})
    db.add(
        Alert(
            type="SYSTEM",
            severity="INFO",
            title="Case registered",
            message=f"Case {row.case_reference} is awaiting veterinary review.",
            district=row.district,
            village=row.village,
            user_id=row.owner_id,
            case_id=row.id,
            created_by=user.id,
        )
    )
    return row, False


async def update(db, user, id, payload):
    row = await get_scoped(db, Case, id, user, lock=True)
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN)
    values = payload.model_dump(exclude_unset=True, exclude_none=True)
    if row.status == "CLOSED":
        raise DomainError("CASE_CLOSED", "Closed cases cannot be edited.", 409)
    if "status" in values or "clinical_assessment" in values:
        require_role(user, Role.VETERINARIAN)
    status = values.get("status", row.status)
    if status != row.status and status not in TRANSITIONS[row.status]:
        raise DomainError("INVALID_TRANSITION", f"Cannot move from {row.status} to {status}.", 409)
    if status == "CONFIRMED" and not values.get("clinical_assessment"):
        raise DomainError("CONFIRMATION_REQUIRED", "An explicit veterinary clinical assessment is required.", 422)
    affected = values.get("affected_count", row.affected_count)
    deaths = values.get("death_count", row.death_count)
    if deaths > affected or (row.animal_id and affected != 1):
        raise DomainError("INVALID_COUNTS", "Counts are inconsistent with the case subject.", 422)
    if row.herd_id:
        herd = await subject(db, user, herd_id=row.herd_id)
        if affected > herd.animal_count:
            raise DomainError("COUNT_EXCEEDS_HERD", "Affected count exceeds herd size.", 422)
    before = row.status
    for key, value in values.items():
        setattr(row, key, value)
    if "severity" in values:
        row.risk_level = (
            "HIGH" if row.severity in ("URGENT", "CRITICAL") else "MEDIUM" if row.severity == "MODERATE" else "LOW"
        )
    row.updated_by = user.id
    audit(db, user, "case_updated", row, {"previous_status": before, "status": row.status})
    if before != row.status:
        db.add(
            Alert(
                type="SYSTEM",
                severity="INFO",
                title="Case status updated",
                message=f"{row.case_reference}: {row.status}",
                district=row.district,
                user_id=row.owner_id,
                case_id=row.id,
                created_by=user.id,
            )
        )
    await flush_refresh(db, row)
    return row


async def assign(db, user, id, vet_id):
    require_role(user, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    row = await get_scoped(db, Case, id, user, lock=True)
    vet = await db.get(User, vet_id)
    if not vet or not vet.is_active or vet.role != Role.VETERINARIAN or vet.district != row.district:
        raise DomainError("INVALID_VETERINARIAN", "Select an active veterinarian in the case district.", 422)
    row.assigned_veterinarian_id = vet.id
    audit(db, user, "assigned", row, {"veterinarian_id": str(vet.id)})
    await flush_refresh(db, row)
    return row


async def escalate(db, user, id, notes, assistance=False):
    row = await get_scoped(db, Case, id, user, lock=True)
    if not assistance:
        require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    if not assistance:
        row.escalated = True
    audit(db, user, "assistance_requested" if assistance else "escalated", row, {"notes": notes})
    db.add(
        Alert(
            type="SYSTEM",
            severity="HIGH" if not assistance else "INFO",
            title="Veterinary review requested",
            message=f"Review requested for {row.case_reference}.",
            district=row.district,
            user_id=row.owner_id,
            case_id=row.id,
            created_by=user.id,
        )
    )
    await flush_refresh(db, row)
    return row


async def timeline(db, user, id):
    await get_scoped(db, Case, id, user)
    return (
        await db.scalars(
            select(AuditLog)
            .where(AuditLog.entity_id == id, AuditLog.entity_type == "cases")
            .order_by(AuditLog.created_at)
            .limit(500)
        )
    ).all()
