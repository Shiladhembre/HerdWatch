# LIVESTOCK SURVEILLANCE PROJECT TEST REPORT

Executed locally on 2026-09-30. **Partial verification; full end-to-end success is blocked by unavailable PostgreSQL and a missing trained image artifact.** No models were retrained, replaced, or deleted. No secret values are included.

## Environment

| Item | Observed result |
|---|---|
| Python | Project virtual environment 3.13.2; system Python 3.14.2 |
| pip | System 25.3; project `pip check`: no broken requirements |
| Node / npm | 22.18.0 / 10.9.3 |
| Database | PostgreSQL/PostGIS configured on localhost:5432; connections time out over IPv4 and IPv6, including outside sandbox |
| Backend | FastAPI 0.141.1; Uvicorn startup and restart completed |
| Frontend | React 19.3.0 / Vite 6.4.3; build, lint, tests, dev-server HTTP passed |
| ML dependencies | TensorFlow 2.21.0 (import executed), NumPy 2.5.3, Pillow 12.3.0, scikit-learn 1.6.1, joblib 1.6.0, python-multipart 0.0.32 |

Dependencies were already installed. No arbitrary upgrades or reinstall were performed. Installed scikit-learn matches the symptom artifact metadata and requirements exactly.

## Project audit and configuration

- Frontend: `frontend/`; React entry `src/main.jsx`, routes `src/App.jsx`, Axios client `src/services/api.js`. Vite scripts: dev, build, preview, lint, test.
- Backend: `backend/`; entry `app.main:app`; routers under `app/api/routes`, assembled by `app/api/router.py`; schemas under `app/schemas`; services under `app/services`.
- ML: symptom registry/predictor under `app/ml`; independent image classifier at `app/services/cattle_image_classifier.py`. An additional outbreak service exists but its model is unconfigured.
- Database: async SQLAlchemy with psycopg, PostgreSQL/PostGIS; 19 ORM application tables. Alembic imports `app.models`, and the frozen `0001_initial` migration explicitly creates application tables and PostGIS. Repository HEAD is `0001_initial`.
- Authentication: Argon2 password hashing, signed access/refresh JWTs, database-backed revocable sessions, owner/district scope. Roles: FARMER, FIELD_WORKER, VETERINARIAN, DISTRICT_OFFICER, ADMIN.
- API base URL: `http://localhost:8000/api/v1`; backend prefix `/api/v1`; explicit CORS origin `http://localhost:5173`.
- Existing tests: backend unit and PostgreSQL integration tests; frontend Node service tests. No browser automation suite or type-check script is configured.
- Required backend settings validate; database URL and JWT secret are present. Artifact trust is enabled. No secret values printed.
- Actual symptom path: `backend/models/livestock_disease_model.pkl`; encoder: `backend/models/disease_label_encoder.pkl`.
- Image classes: `backend/models/cattle_image/cattle_disease_classes.json` exists. `backend/models/cattle_image/cattle_disease_image_model.keras` does **not** exist.
- Image upload maximum 10 MiB, general upload maximum 5 MiB, image confidence threshold 0.70. Multipart image body has a separate bounded limit.
- Frontend `.env` uses `VITE_DEMO_MODE=true`. Live inference is intentionally disabled in demo mode. No verified meanings for G01–G18 exist; live symptom selection is intentionally disabled. These safeguards were preserved.

Startup from each directory:

```powershell
# backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# frontend
npm run dev -- --host 127.0.0.1
```

## BACKEND

Passed: imports, startup, restart, router registration, OpenAPI, Swagger HTML, compilation, Ruff after fixes. OpenAPI contains 70 operations. `/` returns the expected 404 because there is no root handler; `/docs` and `/openapi.json` return 200.

Live HTTP matrix: **72 passed, 1 failed readiness check**, recorded in `QA_ENDPOINT_RESULTS.csv`. All 65 protected operations returned 401 without credentials. Allowed and disallowed CORS preflights passed. Valid symptom/image payloads without a session also returned 401. These checks verify authentication boundaries, **not** successful CRUD or authenticated inference.

Failed: `/health` returns 503 with `database=unavailable_or_unmigrated`, PostGIS unavailable, symptom loaded, image unloaded. This is accurate degraded behavior, not application readiness.

## DATABASE

Passed: static model registration/migration inspection and `alembic heads` reporting `0001_initial`. Regression tests verify readiness rejects absent tables and stale migration revisions.

Failed/blocked: live connectivity, `alembic upgrade head`, applied HEAD verification, actual table existence, read/write/rollback lifecycle, and all four integration fixtures. Connection timeouts persisted outside the sandbox. Docker CLI exists, but its Linux engine pipe is absent and its service is stopped. No database data was deleted. Table existence is **not** inferred from migration source or `alembic_version`.

## SYMPTOM ML MODEL

- Model loaded: **YES**, actual artifact and encoder, using checksum/metadata/version validation.
- 18-feature validation: **PASS**. HTTP tests reject missing/extra fields, strings, negative values, values above 1, null, empty body, malformed JSON. Invalid feature count is rejected by the real predictor.
- Prediction: actual all-zero coded input returned `FMD`, with no invented confidence. This is only an inference smoke check, not a diagnosis or accuracy evaluation.
- Known classes: Antraks, FMD, Leptospirosis, Mastitis, Piroplasmosis, Surra.
- HTTP success contract: **PASS with test-double inference and isolated authentication/persistence**; schema validated with `AssessmentView`, model feature order and persistence call checked. Missing model returns 503.
- Result: real model inference works; live authenticated/persisted API success remains blocked by PostgreSQL.

## IMAGE ML MODEL

- Model loaded: **NO**, trained `.keras` artifact missing. TensorFlow itself imports successfully.
- Input shape: service tests enforce `(None,224,224,3)`; real model shape cannot be inspected.
- Classes: JSON maps foot-and-mouth, healthy, lumpy to indices 0, 1, 2.
- Prediction API: mocked-inference tests pass for JPEG, PNG, WebP, response schema, three probabilities in [0,1], approximately unit sum, display names, screening disclaimer, high/low confidence, and preserving the predicted class when confidence is low.
- Negative tests pass for corrupt/truncated bytes, empty upload, unsupported MIME/format, missing multipart field, file/body size limits, missing/corrupt model, invalid outputs, and decoded-pixel limit. Error responses tested do not expose raw tracebacks. Test image inputs are generated fixtures, **not real cattle photos**.
- Preprocessing tested: decode, RGB conversion, nearest resize to 224x224, float32 array, batch dimension, pixels retained in [0,255]. No extra `/255` normalization added.
- Successful Colab inference/training code is not in the inspected project; exact training parity cannot be established from metadata alone.
- Model loading is locked and attempted once per classifier instance; concurrent mocked test verifies one loader call for eight predictions.
- Performance: real sequential warm-up/inference latency **not measured**, because there is no image artifact. No mock timing is presented as model performance.
- Result: upload/contract/error behavior passes isolated tests; actual cattle image inference remains unverified. The optional real-model test was explicitly enabled and skipped for the missing artifact.
- Reported 93.67% remains validation accuracy, not independent test accuracy.

## AUTHENTICATION

Passed: password hashing/verification, JWT signature/type, expired/invalid/missing token rejection, unit owner/district/role checks, and live missing-token checks for protected routes.

Blocked: registration, login, valid database session, refresh rotation, logout, and complete multi-role authorization workflows. The existing integration suite covers several such flows but all four tests errored before their assertions due to PostgreSQL connectivity. No authentication rules were weakened.

## FRONTEND

- Build: **PASS**, `npm run build` completed (2407 modules; 16.62 seconds).
- Lint: **PASS**, including final rerun.
- Tests: **5 passed**, including final rerun.
- API integration: service tests verify envelope parsing, multipart `file`, bearer token, upload validation and safe error messaging. Static tracing confirms `/predict/disease` sends `symptoms` and `/predict/image` sends multipart data without forcing a JSON content type.
- Runtime serving: Vite starts and GET `/` returns 200 with the React entry reference.
- Browser workflows: **NOT VERIFIED**. In-app browser creation timed out waiting for webview attachment; subsequent tab inventory was empty. No visual navigation, forms, loading states, browser-console checks, or successful rendered inference is claimed.
- Live end-to-end integration: **BLOCKED**, because demo mode is configured, symptom mappings are unverified, PostgreSQL is unreachable, and the image artifact is missing.
- Wording reviewed in screening UI/API distinguishes suspected conditions and model confidence from diagnosis and recommends veterinary confirmation. ML output does not automatically generate medication or dosage; treatment records use separate role-controlled workflows.

## AUTOMATED TESTS

Final complete backend command (image smoke explicitly enabled):

```powershell
$env:RUN_IMAGE_MODEL_SMOKE='1'
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short -ra --junitxml=qa-final.xml
```

| Suite | Passed | Assertion failures | Setup errors | Skipped | Runner warnings |
|---|---:|---:|---:|---:|---:|
| Backend, 73 collected | 68 | 0 | 4 | 1 | 0 |
| Frontend, 5 collected | 5 | 0 | 0 | 0 | 0 |

Backend elapsed 78.33 seconds. TensorFlow emits oneDNN informational runtime messages; these are separate from test-runner warnings. The complete suite is **not all passing**.

Baseline outside sandbox was 51 passed, 1 skipped, 4 setup errors. The 17 added tests include 14 symptom/token/real-model checks and 3 health-readiness checks. Two readiness tests first failed with unexpected 200 responses, then passed after the fix.

Initial sandbox runs also encountered pytest temporary-directory permission errors and Node/esbuild `spawn EPERM`; authorized outside-sandbox reruns resolved those execution restrictions. They were not treated as application defects.

## ISSUES FOUND

1. Missing trained image model prevents real image inference and latency measurement.
2. PostgreSQL is unreachable; migrations and database workflows cannot complete.
3. Health could falsely report ready with no application tables or a stale migration revision.
4. Missing HTTP symptom validation/expired-token regression coverage.
5. Seven existing application Ruff E401 import-style violations.
6. Frontend is configured for demo use, and verified symptom mappings are absent.

## FIXES APPLIED

1. `backend/app/api/routes/health.py`: require all 19 ORM tables and the repository migration head before readiness succeeds. Existing health response fields and ML degradation semantics preserved.
2. `backend/tests/unit/test_health_readiness.py`: regression cases for missing tables, stale revision, and complete schema.
3. `backend/tests/unit/test_prediction_api.py`: symptom success/negative/unavailable API contracts, missing/invalid/expired JWT checks, and a real symptom-model smoke test.
4. Split combined imports in seven application files using Ruff's focused automatic fix; no behavioral rewrite.
5. Added reproducible `backend/scripts/qa_http.py` and per-route `QA_ENDPOINT_RESULTS.csv` evidence.

## FINAL CLEAN START

Stopped the Uvicorn process started for this task and launched a new process. Startup completed, symptom artifact loaded again, and missing image artifact was logged internally. Repeated the HTTP matrix: 72 passed, 1 failed readiness check. Valid prediction payloads are rejected with 401 without a database-backed session; successful authenticated predictions cannot be confirmed. Frontend build and dev-server startup configuration passed; final frontend tests/lint passed.

## REMAINING LIMITATIONS

1. Provide the trained `.keras` file at the configured path (or a valid path override) and the successful Colab inference code plus a cattle JPEG fixture.
2. Restore the configured development PostgreSQL/PostGIS service, migrate it and a dedicated `_test` database, then rerun integration tests and successful authenticated endpoint/CRUD checks. No migration success is claimed.
3. Supply verified G01–G18 meanings before enabling symptom selection; select live frontend mode when ready to test actual APIs.
4. Browser visual/runtime verification needs a functioning browser attachment. Independent model accuracy and real image latency were not evaluated.

## FINAL STATUS

| Requested status | Result |
|---|---|
| Core application runnable | **NO as a complete system**; backend/frontend processes start in degraded/demo state |
| Database functional | **NO in this tested environment** |
| Symptom prediction functional | **YES at real model level; NO verified live end-to-end API workflow** |
| Image prediction functional | **NO**, trained artifact absent |
| Frontend build successful | **YES** |

Evidence: `backend/qa-final.log`, `backend/qa-final.xml`, `backend/qa-baseline.log`, `backend/qa-migration.log`, `QA_ENDPOINT_RESULTS.csv`.
