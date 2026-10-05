import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import numpy as np
import pytest
from PIL import Image

from app.config import get_settings
from app.core.exceptions import DomainError
from app.dependencies import current_user
from app.main import app
from app.schemas.image_prediction import ImagePredictionResponse
from app.services.cattle_image_classifier import (
    CLASSES, CattleImageClassifier, get_image_classifier, resolve_artifact,
)


def image_bytes(fmt="PNG", mode="RGB"):
    buffer = io.BytesIO()
    Image.new(mode, (32, 24), 255 if mode == "L" else (255, 128, 0)).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def service(tmp_path, monkeypatch):
    model_path = tmp_path / "model.keras"
    model_path.write_bytes(b"test double only")
    metadata_path = tmp_path / "classes.json"
    metadata_path.write_text(json.dumps({"classes": list(CLASSES),
        "class_to_index": {name: i for i, name in enumerate(CLASSES)}, "image_size": [224, 224]}))
    config = get_settings().model_copy(update={"image_model_path": model_path, "image_classes_path": metadata_path})
    fake = Mock(input_shape=(None, 224, 224, 3), output_shape=(None, 3))
    fake.predict.return_value = np.array([[0.05, 0.9, 0.05]])
    loader = Mock(return_value=fake)
    monkeypatch.setattr("app.services.cattle_image_classifier.load_keras_model", loader)
    instance = CattleImageClassifier(config)
    instance.test_loader = loader
    return instance


@pytest.fixture
async def client(service):
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(id="test-user")
    app.dependency_overrides[get_image_classifier] = lambda: service
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize("fmt,mime", [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")])
async def test_valid_response(client, service, fmt, mime):
    response = await client.post("/api/v1/predict/image", files={"file": ("../../cow", image_bytes(fmt), mime)})
    assert response.status_code == 200, response.text
    body = response.json()
    ImagePredictionResponse.model_validate(body)
    assert set(body["probabilities"]) == set(CLASSES)
    assert all(0 <= value <= 1 for value in body["probabilities"].values())
    assert sum(body["probabilities"].values()) == pytest.approx(1)
    assert body["prediction"]["class"] in CLASSES
    assert body["prediction"]["confidence_percent"] == 90
    assert body["prediction"]["low_confidence"] is False
    assert "not a veterinary diagnosis" in body["disclaimer"]
    batch = service._model.predict.call_args.args[0]
    assert batch.shape == (1, 224, 224, 3) and batch.dtype == np.float32
    assert batch.max() > 200  # catches accidental /255 normalization


@pytest.mark.parametrize("data,mime,status", [
    (b"broken", "image/png", 400), (b"", "image/jpeg", 400),
    (b"text", "text/plain", 415), (image_bytes("BMP"), "image/png", 415),
    (image_bytes("PNG")[:40], "image/png", 400),
])
async def test_bad_upload(client, data, mime, status):
    response = await client.post("/api/v1/predict/image", files={"file": ("cow", data, mime)})
    assert response.status_code == status, response.text
    assert response.json()["success"] is False


async def test_missing(client):
    assert (await client.post("/api/v1/predict/image")).status_code == 400


async def test_oversized_file(client, service):
    service.settings.image_max_upload_bytes = 1024
    result = await client.post("/api/v1/predict/image", files={"file": ("cow", b"a" * 1025, "image/png")})
    assert result.status_code == 413


async def test_chunked_body_limit(client):
    async def chunks():
        for _ in range(12):
            yield b"x" * 1024 * 1024
    result = await client.post("/api/v1/predict/image", content=chunks(),
                               headers={"Content-Type": "multipart/form-data; boundary=x"})
    assert result.status_code == 413


async def test_over_old_7mb_limit(client):
    data = image_bytes() + b"\0" * 7_000_000
    result = await client.post("/api/v1/predict/image", files={"file": ("cow", data, "image/png")})
    assert result.status_code == 200


async def test_unavailable(client, service):
    service.settings.image_model_path = Path("missing-artifact.keras")
    response = await client.post("/api/v1/predict/image", files={"file": ("cow", image_bytes(), "image/png")})
    assert response.status_code == 503
    assert "missing-artifact" not in response.text
    assert "temporarily unavailable" in response.text


async def test_low_confidence(client, service):
    service.test_loader.return_value.predict.return_value = [[0.34, 0.33, 0.33]]
    result = await client.post("/api/v1/predict/image", files={"file": ("cow", image_bytes(), "image/png")})
    assert result.status_code == 200
    body = result.json()
    assert body["prediction"]["low_confidence"] is True
    assert body["prediction"]["class"] == "foot-and-mouth"
    assert "uncertain" in body["message"]


@pytest.mark.parametrize("output", [[[1, 0]], [[float("nan"), 0, 1]], [[-0.1, 0.2, 0.9]],
                                     [[0.2, 0.2, 0.2]], [[2, 0, 0]]])
async def test_invalid_predictions(client, service, output):
    service.test_loader.return_value.predict.return_value = output
    result = await client.post("/api/v1/predict/image", files={"file": ("cow", image_bytes(), "image/png")})
    assert result.status_code == 500
    assert "traceback" not in result.text.lower()


def test_load_once_concurrently(service):
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: service.predict(image_bytes()), range(8)))
    assert service.test_loader.call_count == 1
    assert service.status == {"loaded": True, "classes": 3}


@pytest.mark.parametrize("changes", [{"classes": ["healthy"]}, {"class_to_index": {}}, {"image_size": [128, 128]}])
def test_invalid_metadata(service, changes):
    path = service.settings.image_classes_path
    data = json.loads(path.read_text())
    path.write_text(json.dumps(data | changes))
    service.load()
    assert not service.status["loaded"]
    service.test_loader.assert_not_called()


def test_bad_model_and_no_retry(service):
    service.test_loader.side_effect = ValueError("corrupt keras file")
    service.load()
    service.load()
    assert not service.status["loaded"] and service.test_loader.call_count == 1


def test_model_shape(service):
    service.test_loader.return_value.output_shape = (None, 6)
    service.load()
    assert not service.status["loaded"]


def test_class_order(service):
    classes = list(reversed(CLASSES))
    service.settings.image_classes_path.write_text(json.dumps({"classes": classes,
        "class_to_index": {name: i for i, name in enumerate(classes)}, "image_size": [224, 224]}))
    service.test_loader.return_value.predict.return_value = [[0.9, 0.05, 0.05]]
    assert service.predict(image_bytes())["prediction"]["class"] == "lumpy"


def test_pixel_limit(service):
    service.settings.image_max_pixels = 100
    with pytest.raises(DomainError) as exc:
        service.preprocess(image_bytes())
    assert exc.value.status == 400


def test_rgb_and_path_independence(service, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resolve_artifact("models/cattle_image/cattle_disease_classes.json").is_file()
    assert service.preprocess(image_bytes(mode="L")).shape == (1, 224, 224, 3)


async def test_docs_and_existing_routes(client):
    assert (await client.get("/docs")).status_code == 200
    spec = (await client.get("/openapi.json")).json()
    for path in ("/api/v1/predict/disease", "/api/v1/predict/outbreak-risk", "/api/v1/animals", "/health"):
        assert path in spec["paths"]
    route = spec["paths"]["/api/v1/predict/image"]["post"]
    assert "multipart/form-data" in route["requestBody"]["content"]
    assert (await client.get("/api/v1/predict/symptom-config")).status_code == 200


async def test_authentication_required(client):
    app.dependency_overrides.pop(current_user)
    result = await client.post("/api/v1/predict/image", files={"file": ("cow", image_bytes(), "image/png")})
    assert result.status_code == 401


def test_optional_real_model():
    if os.getenv("RUN_IMAGE_MODEL_SMOKE") != "1":
        pytest.skip("Set RUN_IMAGE_MODEL_SMOKE=1 for real TensorFlow inference")
    settings = get_settings()
    if not resolve_artifact(settings.image_model_path).is_file():
        pytest.skip("Real image model artifact is unavailable")
    pytest.importorskip("tensorflow")
    result = CattleImageClassifier(settings).predict(image_bytes())
    ImagePredictionResponse.model_validate(result)
