import json
from sqlalchemy import select, func
from app.models import Case
from app.core.constants import Role
from app.core.permissions import require_role
from app.repositories.base import filtered


async def geojson(db, user, filters):
    stmt = (
        filtered(Case, user, filters)
        .with_only_columns(
            Case.id,
            Case.case_reference,
            Case.district,
            Case.village,
            Case.species,
            Case.suspected_disease,
            Case.risk_level,
            Case.affected_count,
            Case.death_count,
            Case.status,
            Case.created_at,
            func.ST_AsGeoJSON(Case.geom).label("geometry"),
        )
        .where(Case.geom.is_not(None))
        .order_by(Case.created_at.desc())
        .limit(2000)
    )
    rows = (await db.execute(stmt)).mappings().all()
    features = []
    for row in rows:
        properties = {
            k: (v.isoformat() if hasattr(v, "isoformat") else str(v) if k == "id" else v)
            for k, v in row.items()
            if k != "geometry"
        }
        features.append(
            {"type": "Feature", "id": str(row["id"]), "geometry": json.loads(row["geometry"]), "properties": properties}
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "limit": 2000,
        "possibly_truncated": len(features) == 2000,
        "privacy": "Authenticated scoped reports; no farmer names or contacts.",
    }


async def hotspots(db, user, filters):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    sub = filtered(Case, user, filters).subquery()
    grid = func.ST_SnapToGrid(sub.c.geom, 0.05)
    stmt = (
        select(
            func.ST_AsGeoJSON(grid).label("geometry"),
            func.count().label("report_count"),
            func.sum(sub.c.affected_count).label("affected_count"),
        )
        .where(sub.c.geom.is_not(None))
        .group_by(grid)
        .having(func.count() >= 3)
        .limit(1000)
    )
    rows = (await db.execute(stmt)).mappings().all()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(r["geometry"]),
                "properties": {
                    "report_count": r["report_count"],
                    "affected_count": r["affected_count"],
                    "interpretation": "Spatial report aggregation; not a confirmed outbreak",
                },
            }
            for r in rows
        ],
        "grid_degrees": 0.05,
        "minimum_reports": 3,
    }
