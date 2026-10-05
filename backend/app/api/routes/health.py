from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from pathlib import Path
from functools import lru_cache
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.database import Base, SessionLocal
import app.models  # noqa: F401
from app.ml.model_loader import registry
from app.services.cattle_image_classifier import classifier

router = APIRouter(tags=["Health"])


@lru_cache
def migration_heads():
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[3] / "alembic"))
    return set(ScriptDirectory.from_config(config).get_heads())


@router.get("/health")
async def health():
    database = "unavailable"
    postgis = "unavailable"
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            database = "connected"
            await db.execute(text("SELECT PostGIS_Version()"))
            postgis = "available"
            revisions = set((await db.execute(text("SELECT version_num FROM alembic_version"))).scalars().all())
            tables = set((await db.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            ))).scalars().all())
            if revisions != migration_heads() or not set(Base.metadata.tables).issubset(tables):
                database = "unavailable_or_unmigrated"
    except Exception:
        database = "unavailable_or_unmigrated"
    ready = (database == "connected" and postgis == "available"
             and registry.symptom.status == "loaded" and classifier.status["loaded"])
    return JSONResponse(
        {
            "status": "healthy" if ready else "degraded",
            "database": database,
            "postgis": postgis,
            "symptom_model": registry.symptom.status,
            "outbreak_model": registry.outbreak.status,
            "cattle_image_model": classifier.status,
            "version": "1.0.0",
        },
        status_code=200 if ready else 503,
    )
