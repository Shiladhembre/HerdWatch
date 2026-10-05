"""HTTP contract tests; authentication/persistence are isolated, not claimed as DB E2E."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import jwt
import pytest

from app.config import get_settings
from app.core.exceptions import DomainError
from app.core.security import create_token, decode_token
from app.core.symptom_config import FEATURE_CODES
from app.database import get_db
from app.dependencies import current_user
from app.main import app
from app.ml.metadata import ModelContract
from app.ml.model_loader import ModelRegistry, ModelSlot, registry
from app.ml.symptom_predictor import predict
from app.schemas.prediction import AssessmentView


@pytest.fixture
async def prediction_client(monkeypatch):
    db = SimpleNamespace(add=Mock(), flush=AsyncMock())
    async def database():
        yield db
    user = SimpleNamespace(id=uuid4(), role="FARMER", district="Pune")
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[current_user] = lambda: user
    model = Mock()
    model.predict.return_value = ["FMD"]
    slot = ModelSlot(model=model, status="loaded", contract=ModelContract(
        name="test-double", version="test", features=FEATURE_CODES, classes=["FMD"]))
    monkeypatch.setattr(registry, "symptom", slot)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield client, db, slot
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


async def test_symptom_success_contract(prediction_client):
    client, db, slot = prediction_client
    response = await client.post("/api/v1/predict/disease", json={"symptoms": dict.fromkeys(FEATURE_CODES, 0)})
    assert response.status_code == 200
    result = AssessmentView.model_validate(response.json()["data"])
    assert result.suspected_disease in slot.contract.classes
    assert result.veterinary_confirmation_required and result.confidence is None
    db.flush.assert_awaited_once()
    assert list(slot.model.predict.call_args.args[0].columns) == FEATURE_CODES


@pytest.mark.parametrize("kind", ["missing", "extra", "string", "negative", "large", "null", "empty", "malformed"])
async def test_symptom_invalid_http(prediction_client, kind):
    client, db, slot = prediction_client
    features = dict.fromkeys(FEATURE_CODES, 0)
    if kind == "missing":
        features.pop("G18")
    elif kind == "extra":
        features["G19"] = 0
    elif kind in {"string", "negative", "large", "null"}:
        features["G01"] = {"string": "1", "negative": -1, "large": 2, "null": None}[kind]
    kwargs = {"json": {} if kind == "empty" else {"symptoms": features}}
    if kind == "malformed":
        kwargs = {"content": b'{"symptoms":', "headers": {"Content-Type": "application/json"}}
    response = await client.post("/api/v1/predict/disease", **kwargs)
    assert response.status_code == 422
    assert "traceback" not in response.text.lower()
    slot.model.predict.assert_not_called()
    db.add.assert_not_called()


async def test_symptom_unavailable_http(prediction_client):
    client, db, slot = prediction_client
    slot.model = None
    response = await client.post("/api/v1/predict/disease", json={"symptoms": dict.fromkeys(FEATURE_CODES, 0)})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_NOT_AVAILABLE"
    db.add.assert_not_called()


@pytest.mark.parametrize("token", [None, "invalid", "expired"])
async def test_protected_route_rejects_tokens(prediction_client, token):
    client, db, _ = prediction_client
    app.dependency_overrides.pop(current_user)
    if token == "expired":
        _, claims = create_token(uuid4(), uuid4())
        claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        token = jwt.encode(claims, get_settings().jwt_secret_key.get_secret_value(), algorithm="HS256")
        with pytest.raises(DomainError):
            decode_token(token)
    headers = {"Authorization": "Bearer " + token} if token else {}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_real_symptom_model_smoke():
    """Actual shipped artifact, no training and no mocked inference."""
    loaded = ModelRegistry()
    loaded.load()
    if loaded.symptom.status == "not_configured":
        pytest.skip("Real symptom artifact unavailable")
    assert loaded.symptom.status == "loaded"
    assert loaded.symptom.model.n_features_in_ == 18
    assert len(loaded.symptom.encoder.classes_) == 6
    label, _ = predict(loaded.symptom, dict.fromkeys(FEATURE_CODES, 0))
    assert label in loaded.symptom.encoder.classes_
    with pytest.raises(DomainError):
        predict(loaded.symptom, {"G01": 0})
