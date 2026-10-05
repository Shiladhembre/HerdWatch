import math
from datetime import datetime, time, timedelta, timezone
from sqlalchemy import select, func, or_
from app.core.permissions import scope
from app.core.exceptions import DomainError


def filtered(model, user, filters, owner_column="owner_id"):
    stmt = select(model).where(scope(model, user, owner_column))
    for key in ["state", "district", "block", "village", "species", "status"]:
        value = getattr(filters, key, None)
        if value and hasattr(model, key):
            stmt = stmt.where(getattr(model, key) == value)
    if filters.disease and hasattr(model, "suspected_disease"):
        stmt = stmt.where(model.suspected_disease == filters.disease)
    if filters.risk and hasattr(model, "risk_level"):
        stmt = stmt.where(model.risk_level == filters.risk.upper())
    if filters.start_date:
        stmt = stmt.where(model.created_at >= datetime.combine(filters.start_date, time.min, timezone.utc))
    if filters.end_date:
        stmt = stmt.where(
            model.created_at < datetime.combine(filters.end_date + timedelta(days=1), time.min, timezone.utc)
        )
    if filters.search:
        columns = [
            getattr(model, k)
            for k in ["case_reference", "animal_tag", "herd_name", "village", "suspected_disease"]
            if hasattr(model, k)
        ]
        if columns:
            stmt = stmt.where(
                or_(
                    *(
                        c.ilike("%" + filters.search.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\")
                        for c in columns
                    )
                )
            )
    return stmt


async def paginate(db, stmt, filters):
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = (await db.scalars(stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size))).all()
    return {
        "items": items,
        "page": filters.page,
        "page_size": filters.page_size,
        "total": total,
        "pages": math.ceil(total / filters.page_size),
    }


async def flush_refresh(db, obj):
    # An UPDATE with a server-side onupdate expires updated_at; reload so the
    # synchronous serializer can read it without lazy IO outside a greenlet.
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_scoped(db, model, id, user, owner_column="owner_id", lock=False):
    stmt = select(model).where(model.id == id, scope(model, user, owner_column))
    if lock:
        stmt = stmt.with_for_update()
    item = await db.scalar(stmt)
    if item is None:
        raise DomainError("NOT_FOUND", "Record not found.", 404)
    return item
