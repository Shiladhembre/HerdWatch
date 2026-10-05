import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.routes import health
from app.database import Base


@pytest.mark.parametrize("missing,revision,status", [(True, "0001_initial", 503), (False, "old", 503), (False, "0001_initial", 200)])
async def test_readiness_requires_application_tables_and_head(monkeypatch, missing, revision, status):
    db = AsyncMock()
    async def execute(statement, *args, **kwargs):
        result = MagicMock()
        sql = str(statement)
        if "pg_tables" in sql:
            tables = [] if missing else list(Base.metadata.tables)
            result.scalars.return_value.all.return_value = tables
        elif "alembic_version" in sql:
            result.scalars.return_value.all.return_value = [revision]
        return result
    db.execute.side_effect = execute
    session = MagicMock()
    session.return_value.__aenter__ = AsyncMock(return_value=db)
    session.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(health, "SessionLocal", session)
    monkeypatch.setattr(health.registry.symptom, "status", "loaded")
    monkeypatch.setattr(health.classifier, "_model", object())
    response = await health.health()
    assert response.status_code == status
    assert json.loads(response.body)["status"] == ("healthy" if status == 200 else "degraded")


@pytest.mark.parametrize("symptom,image", [("not_configured", True), ("loaded", False)])
async def test_missing_prediction_model_degrades_readiness(monkeypatch, symptom, image):
    db = AsyncMock()
    async def execute(statement):
        result = MagicMock()
        values = list(Base.metadata.tables) if "pg_tables" in str(statement) else list(health.migration_heads())
        result.scalars.return_value.all.return_value = values
        return result
    db.execute.side_effect = execute
    session = MagicMock()
    session.return_value.__aenter__ = AsyncMock(return_value=db)
    session.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(health, "SessionLocal", session)
    monkeypatch.setattr(health.registry.symptom, "status", symptom)
    monkeypatch.setattr(health.classifier, "_model", object() if image else None)
    response = await health.health()
    assert response.status_code == 503
    assert json.loads(response.body)["status"] == "degraded"
