from datetime import date
from sqlalchemy import select, func, distinct
from app.models import Case, Animal, LabReferral, Vaccination, Outbreak
from app.core.permissions import scope
from app.core.constants import Role
from app.repositories.base import filtered
from app.utils.serialization import record


async def count(db, model, user, *conditions):
    return await db.scalar(select(func.count()).select_from(model).where(scope(model, user), *conditions)) or 0


async def grouped(db, user, filters, key):
    sub = filtered(Case, user, filters).subquery()
    column = {
        "disease": sub.c.suspected_disease,
        "species": sub.c.species,
        "risk": sub.c.risk_level,
        "date": func.date(sub.c.created_at),
        "village": sub.c.village,
    }[key]
    value = func.count()
    rows = (
        (await db.execute(select(column.label("name"), value.label("value")).group_by(column).order_by(column)))
        .mappings()
        .all()
    )
    return [{"name": str(r["name"] or "Awaiting assessment"), "value": r["value"]} for r in rows]


async def trends(db, user, filters):
    sub = filtered(Case, user, filters).subquery()
    day = func.date(sub.c.created_at)
    return [
        dict(r)
        for r in (
            await db.execute(
                select(day.label("date"), func.count().label("cases"), func.sum(sub.c.death_count).label("mortality"))
                .group_by(day)
                .order_by(day)
            )
        ).mappings()
    ]


async def coverage(db, user):
    total = await count(db, Animal, user)
    covered = (
        await db.scalar(
            select(func.count(distinct(Vaccination.animal_id))).where(
                scope(Vaccination, user), Vaccination.animal_id.is_not(None), Vaccination.next_due_on >= date.today()
            )
        )
        or 0
    )
    return {
        "registered_animals": total,
        "animals_with_unexpired_recorded_due_date": covered,
        "coverage_percent": round(100 * covered / total, 2) if total else None,
        "denominator": "registered animals; eligibility rules not configured",
    }


async def dashboard(db, user, filters):
    sub = filtered(Case, user, filters).subquery()
    active = await db.scalar(select(func.count()).select_from(sub).where(sub.c.status.not_in(["RESOLVED", "CLOSED"])))
    high = await db.scalar(select(func.count(distinct(sub.c.village))).where(sub.c.risk_level == "HIGH"))
    outbreaks = (
        0
        if user.role == Role.FARMER
        else await count(db, Outbreak, user, Outbreak.status.in_(["SUSPECTED", "INVESTIGATING"]))
    )
    vaccine = await coverage(db, user)
    recent = (await db.scalars(filtered(Case, user, filters).order_by(Case.created_at.desc()).limit(10))).all()
    return {
        "summary": {
            "active_cases": active,
            "suspected_outbreaks": outbreaks,
            "high_risk_areas": high,
            "animals_monitored": vaccine["registered_animals"],
            "vaccinated_animals": vaccine["animals_with_unexpired_recorded_due_date"],
            "pending_lab_results": await count(
                db, LabReferral, user, LabReferral.status.not_in(["RESULT_AVAILABLE", "CLOSED"])
            ),
        },
        "disease_trend": await trends(db, user, filters),
        "disease_distribution": await grouped(db, user, filters, "disease"),
        "risk_distribution": await grouped(db, user, filters, "risk"),
        "species_distribution": await grouped(db, user, filters, "species"),
        "recent_cases": [record(c) for c in recent],
    }
