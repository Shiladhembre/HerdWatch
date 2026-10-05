from sqlalchemy import select, or_, and_
from sqlalchemy.dialects.postgresql import insert
from app.models import Alert, AlertRead, User, Case, Outbreak
from app.core.constants import Role
from app.core.permissions import require_role, district_allowed
from app.core.exceptions import DomainError
from app.repositories.base import paginate, get_scoped
from app.utils.serialization import record
from .audit_service import audit


def visible(user):
    return (
        and_(Alert.district == user.district, or_(Alert.user_id == user.id, Alert.user_id.is_(None)))
        if user.role != Role.ADMIN
        else True
    )


async def list_alerts(db, user, filters):
    stmt = select(Alert).where(visible(user)).order_by(Alert.created_at.desc())
    result = await paginate(db, stmt, filters)
    ids = [a.id for a in result["items"]]
    reads = (
        set(
            (
                await db.scalars(
                    select(AlertRead.alert_id).where(AlertRead.user_id == user.id, AlertRead.alert_id.in_(ids))
                )
            ).all()
        )
        if ids
        else set()
    )
    result["items"] = [{**record(a), "is_read": a.id in reads} for a in result["items"]]
    return result


async def mark_read(db, user, id):
    row = await db.scalar(select(Alert).where(Alert.id == id, visible(user)))
    if not row:
        raise DomainError("NOT_FOUND", "Alert not found.", 404)
    await db.execute(
        insert(AlertRead)
        .values(alert_id=id, user_id=user.id, is_read=True)
        .on_conflict_do_nothing(index_elements=["alert_id", "user_id"])
    )
    return {**record(row), "is_read": True}


async def create(db, user, payload):
    require_role(user, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    district_allowed(user, payload.district)
    if payload.user_id:
        recipient = await db.get(User, payload.user_id)
        if not recipient or recipient.district != payload.district:
            raise DomainError("INVALID_RECIPIENT", "Recipient must belong to the alert district.", 422)
    if payload.case_id:
        case = await get_scoped(db, Case, payload.case_id, user)
        if case.district != payload.district or payload.user_id != case.owner_id:
            raise DomainError(
                "ALERT_PRIVACY", "Case-specific alerts must target the case owner in the same district.", 422
            )
    if payload.outbreak_id:
        outbreak = await get_scoped(db, Outbreak, payload.outbreak_id, user)
        if outbreak.district != payload.district:
            raise DomainError("DISTRICT_MISMATCH", "Outbreak must match the alert district.", 422)
    row = Alert(**payload.model_dump(), created_by=user.id)
    db.add(row)
    await db.flush()
    audit(db, user, "alert_created", row)
    return row
