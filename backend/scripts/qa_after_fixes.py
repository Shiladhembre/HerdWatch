"""
Comprehensive post-fix QA script.
Run from the backend directory with the virtualenv active:

    python scripts/qa_after_fixes.py

Prerequisites:
    1. PostgreSQL/PostGIS container running and migrated (alembic upgrade head succeeded).
    2. cattle_disease_image_model.keras placed in models/cattle_image/.
    3. uvicorn app.main:app running on 127.0.0.1:8000.

Produces:
    QA_ENDPOINT_RESULTS_AFTER_FIXES.csv   (written to parent directory)
    backend/qa-after-fixes.log             (printed to stdout, tee manually)
"""
from __future__ import annotations
import csv
import io
import json
import sys
import textwrap
import time
from pathlib import Path
from typing import NamedTuple

import httpx
import psycopg
from PIL import Image
from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import get_settings
from app.database import Base
from app.ml.model_loader import ModelRegistry
from app.ml.symptom_predictor import predict as symptom_predict
from app.core.symptom_config import FEATURE_CODES
from app.services.cattle_image_classifier import CattleImageClassifier, resolve_artifact
import app.models  # noqa: F401 – ensure all ORM models are registered

BACKEND_URL = "http://127.0.0.1:8000"
REPORT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Row(NamedTuple):
    section: str
    check: str
    result: str
    detail: str


rows: list[Row] = []


def record(section: str, check: str, ok: bool, detail: str = ""):
    tag = "PASS" if ok else "FAIL"
    rows.append(Row(section, check, tag, detail))
    symbol = "✓" if ok else "✗"
    print(f"  {symbol} [{tag}] {check}: {detail}")
    return ok


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def make_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(180, 120, 60)).save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Database connectivity
# ---------------------------------------------------------------------------

def check_database() -> bool:
    section("1. DATABASE")
    settings = get_settings()
    url = make_url(settings.database_url)
    try:
        with psycopg.connect(
            host=url.host,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            dbname=url.database,
            connect_timeout=5,
        ) as db:
            record("DATABASE", "connection", True, f"host={url.host} db={url.database}")
            row = db.execute("SELECT version()").fetchone()
            record("DATABASE", "pg_version", True, row[0][:60])
            try:
                pgv = db.execute("SELECT PostGIS_Version()").fetchone()[0]
                record("DATABASE", "postgis", True, pgv)
            except Exception as exc:
                record("DATABASE", "postgis", False, str(exc))

            rev = db.execute("SELECT version_num FROM alembic_version").fetchone()
            record("DATABASE", "alembic_version", bool(rev), str(rev[0]) if rev else "NO ROW")

            tables = {r[0] for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
            expected = set(Base.metadata.tables)
            missing = expected - tables
            record("DATABASE", "application_tables_present", not missing,
                   f"expected={len(expected)} missing={sorted(missing) or 'none'}")

            # Read/write rollback probe
            db.execute("CREATE TEMP TABLE qa_probe (v integer)")
            db.execute("INSERT INTO qa_probe VALUES (42)")
            assert db.execute("SELECT v FROM qa_probe").fetchone()[0] == 42
            db.rollback()
            assert db.execute("SELECT to_regclass('qa_probe')").fetchone()[0] is None
            record("DATABASE", "read_write_rollback", True, "temp table created and rolled back cleanly")
            return not missing and rev is not None
    except Exception as exc:
        record("DATABASE", "connection", False, str(exc)[:120])
        return False


# ---------------------------------------------------------------------------
# 2. Symptom model (direct)
# ---------------------------------------------------------------------------

def check_symptom_model() -> bool:
    section("2. SYMPTOM MODEL (direct)")
    reg = ModelRegistry()
    reg.load()
    slot = reg.symptom
    ok1 = record("SYMPTOM_MODEL", "loads", slot.status == "loaded", slot.status)
    if not ok1:
        return False
    ok2 = record("SYMPTOM_MODEL", "18_features", slot.model.n_features_in_ == 18,
                 f"n_features_in_={slot.model.n_features_in_}")
    ok3 = record("SYMPTOM_MODEL", "6_classes", len(slot.encoder.classes_) == 6,
                 f"classes={list(slot.encoder.classes_)}")
    label, conf = symptom_predict(slot, dict.fromkeys(FEATURE_CODES, 0))
    ok4 = record("SYMPTOM_MODEL", "inference", label in slot.encoder.classes_,
                 f"label={label} confidence={conf}")
    return all([ok2, ok3, ok4])


# ---------------------------------------------------------------------------
# 3. Image model (direct)
# ---------------------------------------------------------------------------

def check_image_model() -> bool:
    section("3. IMAGE MODEL (direct)")
    settings = get_settings()
    keras_path = resolve_artifact(settings.image_model_path)
    ok_file = record("IMAGE_MODEL", "artifact_exists", keras_path.is_file(), str(keras_path))
    if not ok_file:
        return False

    clf = CattleImageClassifier(settings)
    clf.load()
    ok_load = record("IMAGE_MODEL", "tf_load", clf._model is not None,
                     "loaded" if clf._model else "FAILED")
    if not ok_load:
        return False

    input_shape = tuple(clf._model.input_shape)
    output_shape = tuple(clf._model.output_shape)
    record("IMAGE_MODEL", "input_shape", input_shape == (None, 224, 224, 3), str(input_shape))
    record("IMAGE_MODEL", "output_classes", output_shape == (None, 3), str(output_shape))
    record("IMAGE_MODEL", "class_order", list(clf._classes) == ["foot-and-mouth", "healthy", "lumpy"],
           str(list(clf._classes)))

    result = clf.predict(make_png())
    probs = result["probabilities"]
    ok_infer = record("IMAGE_MODEL", "inference", result["prediction"]["class"] in clf._classes,
                      f"class={result['prediction']['class']} conf={result['prediction']['confidence']:.3f}")
    record("IMAGE_MODEL", "probabilities_sum", abs(sum(probs.values()) - 1) < 0.01,
           f"sum={sum(probs.values()):.6f}")
    record("IMAGE_MODEL", "disclaimer_present", "veterinary" in result.get("disclaimer", "").lower(), "OK")
    return ok_infer


# ---------------------------------------------------------------------------
# 4–10. Live API checks
# ---------------------------------------------------------------------------

def check_backend_health(client: httpx.Client) -> bool:
    section("4. BACKEND HEALTH ENDPOINTS")
    for path, expected in [("/", 404), ("/docs", 200), ("/openapi.json", 200)]:
        r = client.get(path)
        record("HEALTH", path, r.status_code == expected,
               f"expected={expected} actual={r.status_code}")

    r = client.get("/health")
    body = r.json()
    is_ready = r.status_code == 200
    record("HEALTH", "/health_status", is_ready,
           f"HTTP={r.status_code} status={body.get('status')} db={body.get('database')}")
    record("HEALTH", "/health_database_ready", body.get("database") == "connected", body.get("database"))
    record("HEALTH", "/health_symptom_loaded", body.get("symptom_model") == "loaded",
           str(body.get("symptom_model")))
    record("HEALTH", "/health_image_loaded", body.get("cattle_image_model", {}).get("loaded") is True,
           str(body.get("cattle_image_model")))
    return is_ready


def register_and_login(client: httpx.Client) -> dict | None:
    """Register a fresh test user and return auth headers, or None on failure."""
    import random, string
    uid = "".join(random.choices(string.ascii_lowercase, k=8))
    payload = {
        "full_name": f"QA Tester {uid}",
        "email": f"qa_{uid}@example.com",
        "mobile": f"+91{''.join(random.choices(string.digits, k=10))}",
        "password": "QaPassword-123",
        "role": "FARMER",
        "state": "Maharashtra",
        "district": "Pune",
        "block": "Haveli",
        "village": "QA Village",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    if r.status_code not in (200, 201):
        record("AUTH", "register", False, f"HTTP={r.status_code} {r.text[:80]}")
        return None
    r2 = client.post("/api/v1/auth/login", json={"identifier": payload["email"], "password": payload["password"]})
    if r2.status_code != 200:
        record("AUTH", "login", False, f"HTTP={r2.status_code} {r2.text[:80]}")
        return None
    token = r2.json()["data"]["access_token"]
    record("AUTH", "register+login", True, f"user={payload['email']}")
    return {"Authorization": f"Bearer {token}"}


def check_symptom_api(client: httpx.Client, headers: dict) -> bool:
    section("5. SYMPTOM API (live E2E)")
    ep = "/api/v1/predict/disease"

    # Valid 18-feature request
    r = client.post(ep, json={"symptoms": dict.fromkeys(FEATURE_CODES, 0)}, headers=headers)
    ok = record("SYMPTOM_API", "valid_18_features", r.status_code == 200,
                f"HTTP={r.status_code} {r.text[:120]}")
    if r.status_code == 200:
        body = r.json()
        record("SYMPTOM_API", "response_schema", "suspected_disease" in body.get("data", {}),
               str(body.get("data", {}).get("suspected_disease")))
        record("SYMPTOM_API", "veterinary_flag", body.get("data", {}).get("veterinary_confirmation_required") is True,
               "confirmed")

    # Missing feature
    bad = dict.fromkeys(FEATURE_CODES, 0)
    bad.pop("G18")
    r2 = client.post(ep, json={"symptoms": bad}, headers=headers)
    record("SYMPTOM_API", "missing_feature_422", r2.status_code == 422, f"HTTP={r2.status_code}")

    # Invalid binary value
    inv = dict.fromkeys(FEATURE_CODES, 0)
    inv["G01"] = 5
    r3 = client.post(ep, json={"symptoms": inv}, headers=headers)
    record("SYMPTOM_API", "invalid_value_422", r3.status_code == 422, f"HTTP={r3.status_code}")

    # Malformed JSON
    r4 = client.post(ep, content=b'{"symptoms":', headers=dict(headers, **{"Content-Type": "application/json"}))
    record("SYMPTOM_API", "malformed_json_422", r4.status_code == 422, f"HTTP={r4.status_code}")

    # No auth
    r5 = client.post(ep, json={"symptoms": dict.fromkeys(FEATURE_CODES, 0)})
    record("SYMPTOM_API", "no_auth_401", r5.status_code == 401, f"HTTP={r5.status_code}")
    return ok


def check_image_api(client: httpx.Client, headers: dict) -> bool:
    section("6. IMAGE API (live E2E)")
    ep = "/api/v1/predict/image"

    png = make_png()

    # Valid PNG
    r = client.post(ep, files={"file": ("cow.png", png, "image/png")}, headers=headers)
    ok = record("IMAGE_API", "valid_PNG", r.status_code == 200,
                f"HTTP={r.status_code} {r.text[:120]}")
    if r.status_code == 200:
        body = r.json()
        pred = body.get("prediction", {})
        probs = body.get("probabilities", {})
        record("IMAGE_API", "predicted_class_valid",
               pred.get("class") in ("foot-and-mouth", "healthy", "lumpy"),
               str(pred.get("class")))
        record("IMAGE_API", "probabilities_in_0_1",
               all(0 <= v <= 1 for v in probs.values()) and len(probs) == 3,
               str(probs))
        record("IMAGE_API", "disclaimer_present",
               "veterinary" in body.get("disclaimer", "").lower(), "OK")

    # Valid JPEG
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(100, 200, 100)).save(buf, format="JPEG")
    r_jpg = client.post(ep, files={"file": ("cow.jpg", buf.getvalue(), "image/jpeg")}, headers=headers)
    record("IMAGE_API", "valid_JPEG", r_jpg.status_code == 200, f"HTTP={r_jpg.status_code}")

    # Corrupted image
    r_bad = client.post(ep, files={"file": ("bad.jpg", b"notanimage", "image/jpeg")}, headers=headers)
    record("IMAGE_API", "corrupted_image_400", r_bad.status_code == 400, f"HTTP={r_bad.status_code}")

    # Empty file
    r_empty = client.post(ep, files={"file": ("empty.jpg", b"", "image/jpeg")}, headers=headers)
    record("IMAGE_API", "empty_file_400", r_empty.status_code == 400, f"HTTP={r_empty.status_code}")

    # Unsupported format (BMP renamed to .jpg)
    buf2 = io.BytesIO()
    Image.new("RGB", (32, 32)).save(buf2, format="BMP")
    r_bmp = client.post(ep, files={"file": ("file.jpg", buf2.getvalue(), "image/jpeg")}, headers=headers)
    record("IMAGE_API", "unsupported_bmp_400_or_415", r_bmp.status_code in (400, 415), f"HTTP={r_bmp.status_code}")

    for name, data, mime, expected in [
        ("unsupported.txt", b"text", "text/plain", 415),
        ("renamed.jpg", b"Plain text renamed to JPEG", "image/jpeg", 400),
        ("oversized.jpg", b"x" * (get_settings().image_max_upload_bytes + 1), "image/jpeg", 413),
    ]:
        response = client.post(ep, files={"file": (name, data, mime)}, headers=headers)
        record("IMAGE_API", name, response.status_code == expected, f"HTTP={response.status_code}")

    # Missing multipart field
    r_missing = client.post(ep, headers=headers)
    record("IMAGE_API", "missing_field_400", r_missing.status_code == 400, f"HTTP={r_missing.status_code}")

    # No auth
    r_noauth = client.post(ep, files={"file": ("cow.png", png, "image/png")})
    record("IMAGE_API", "no_auth_401", r_noauth.status_code == 401, f"HTTP={r_noauth.status_code}")

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("  QA REMEDIATION SMOKE TEST")
    print(f"  {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print("="*60)

    db_ok = check_database()
    sym_ok = check_symptom_model()
    img_ok = check_image_model()

    with httpx.Client(base_url=BACKEND_URL, timeout=30) as client:
        try:
            client.get("/health")
            backend_up = True
        except Exception as exc:
            print(f"\nERROR: backend at {BACKEND_URL} is not reachable: {exc}")
            backend_up = False

        if backend_up:
            health_ok = check_backend_health(client)
            auth_headers = register_and_login(client)
            if auth_headers:
                sym_api_ok = check_symptom_api(client, auth_headers)
                img_api_ok = check_image_api(client, auth_headers)
            else:
                section("AUTH FAILED")
                sym_api_ok = img_api_ok = False
                record("AUTH", "register+login", False, "skipped remaining API checks")
        else:
            health_ok = sym_api_ok = img_api_ok = False

    # Write CSV
    csv_path = REPORT_ROOT / "QA_ENDPOINT_RESULTS_AFTER_FIXES_20261001.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Section", "Check", "Result", "Detail"])
        for row in rows:
            w.writerow(list(row))
    print(f"\nCSV written: {csv_path}")

    # Summary
    passed = sum(1 for r in rows if r.result == "PASS")
    failed = sum(1 for r in rows if r.result == "FAIL")
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {passed} passed / {failed} failed")
    print(f"  Database:       {'YES' if db_ok else 'NO'}")
    print(f"  Symptom model:  {'YES' if sym_ok else 'NO'}")
    print(f"  Image model:    {'YES' if img_ok else 'NO'}")
    print(f"  Backend health: {'YES' if health_ok else 'NO'}")
    print(f"  Symptom API:    {'YES' if sym_api_ok else 'NO'}")
    print(f"  Image API:      {'YES' if img_api_ok else 'NO'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
