from datetime import date
from app.models import Outbreak, OutbreakCase, Case, Alert
from app.core.constants import Role
from app.core.permissions import require_role, district_allowed
from app.core.exceptions import DomainError
from app.repositories.base import get_scoped, flush_refresh
from .animal_service import point
from .audit_service import audit


async def create(db, user, payload):
    require_role(user, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    district_allowed(user, payload.district)
    for id in set(payload.case_ids):
        case = await get_scoped(db, Case, id, user)
        if case.district != payload.district:
            raise DomainError("DISTRICT_MISMATCH", "All cases must belong to the outbreak district.", 422)
    row = Outbreak(
        **payload.model_dump(exclude={"case_ids"}),
        created_by=user.id,
        updated_by=user.id,
        geom=point(payload.latitude, payload.longitude),
    )
    db.add(row)
    await db.flush()
    for id in set(payload.case_ids):
        db.add(OutbreakCase(outbreak_id=row.id, case_id=id))
    audit(db, user, "outbreak_suspected", row)
    db.add(
        Alert(
            type="OUTBREAK",
            severity="HIGH",
            title="Suspected outbreak under review",
            message="An authorised team has opened an investigation. This is not a confirmed diagnosis.",
            district=row.district,
            village=row.village,
            outbreak_id=row.id,
            created_by=user.id,
        )
    )
    return row


async def update(db, user, id, payload):
    require_role(user, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    row = await get_scoped(db, Outbreak, id, user)
    allowed = {
        "SUSPECTED": {"INVESTIGATING"},
        "INVESTIGATING": {"CONFIRMED", "RESOLVED"},
        "CONFIRMED": {"RESOLVED"},
        "RESOLVED": set(),
    }
    if payload.status != row.status and payload.status not in allowed[row.status]:
        raise DomainError("INVALID_TRANSITION", "Invalid outbreak status transition.", 409)
    if payload.status == "CONFIRMED":
        require_role(user, Role.VETERINARIAN)
        row.confirmed_by = user.id
        row.confirmed_on = date.today()
    row.status = payload.status
    row.evidence = payload.evidence
    row.updated_by = user.id
    audit(db, user, "outbreak_status_updated", row, {"status": row.status})
    await flush_refresh(db, row)
    return row
