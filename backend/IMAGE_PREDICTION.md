# Cattle image screening API

`POST /api/v1/predict/image` accepts multipart form field `file` (JPEG, PNG or WebP).
Use the existing login endpoint and send its access token as `Authorization: Bearer <token>`.
The route follows `API_V1_PREFIX` and uses the existing authentication and error envelope.
No database schema, symptom/outbreak prediction logic, or stored model contracts were changed.

## Files

```text
backend/
  app/
    api/routes/image_predictions.py       # new authenticated upload route
    api/router.py                        # register route
    config.py                            # image settings
    core/image_upload_middleware.py      # new bounded multipart body handling
    core/middleware.py                   # retain 7 MB limit for other routes
    main.py                              # load classifier once per worker
    api/routes/health.py                  # image readiness field
    schemas/image_prediction.py          # new typed response
    services/cattle_image_classifier.py   # new independent inference service
  models/cattle_image/
    cattle_disease_classes.json           # supplied mapping copied here
    cattle_disease_image_model.keras      # REQUIRED, not supplied/found
  tests/unit/test_cattle_image.py         # API/service tests and optional smoke test
  requirements.txt                       # adds tensorflow==2.21.0 only
  .env.example                           # documents image configuration
  IMAGE_PREDICTION.md                     # this guide
```

Copy the trained `.keras` model into `backend/models/cattle_image/` and restart the server.
Artifact paths are resolved relative to the backend directory, independently of the working directory.
Absolute environment overrides are also supported. Never substitute the symptom `.pkl` files here.
Missing/corrupt artifacts or unavailable TensorFlow are logged internally and yield a safe HTTP 503
for authenticated image requests; other services continue running. A failed load is not retried
per request. Restart after correcting artifacts. Each server worker has its own loaded model.

## Configuration

```dotenv
IMAGE_MODEL_PATH=models/cattle_image/cattle_disease_image_model.keras
IMAGE_CLASSES_PATH=models/cattle_image/cattle_disease_classes.json
IMAGE_MAX_UPLOAD_BYTES=10485760
IMAGE_MAX_PIXELS=20000000
IMAGE_MODEL_CONFIDENCE_THRESHOLD=0.70
```

The file limit is 10 MiB by default. The complete multipart request is bounded to that limit
plus 64 KiB for headers/fields, including requests without Content-Length. File size is checked
separately. Pillow verifies and decodes the image with a decoded-pixel limit. Uploaded filenames
are ignored; no image is permanently stored. FastAPI may temporarily spool multipart uploads.
Inference runs in a thread pool and is serialized per classifier instance.

Preprocessing converts to RGB, resizes to 224x224 using nearest interpolation (the Keras
`load_img` default), then creates float32 `(1,224,224,3)` pixels in `[0,255]`. No additional
normalization is applied. The supplied notebook only contains dataset extraction/validation,
not the final training model or successful Colab single-image test. Exact parity therefore still
requires comparison against that code and the trained artifact, especially resize interpolation.
The reported 93.67% is validation accuracy, not independent test accuracy.

## Run and inspect

Run from the backend directory with the existing `.env` configured:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs, use **Authorize** with an access token, expand
`POST /api/v1/predict/image`, select **Try it out**, choose a file and execute.

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/predict/image" -H "Authorization: Bearer YOUR_ACCESS_TOKEN" -H "accept: application/json" -F "file=@cow.jpg"
```

Let curl set multipart Content-Type and its boundary automatically.

Successful JSON contains `success`, `prediction` (`class`, `display_name`, `confidence`,
`confidence_percent`, `low_confidence`), `probabilities` (exactly `foot-and-mouth`, `healthy`,
`lumpy`), `model` (`name`, ordered `classes`), `message` and `disclaimer`. Probabilities come
from the model without sample values or fabricated predictions. Raw probabilities retain
precision; percentages are rounded to two decimals. Low confidence preserves the predicted
class and advises veterinary assessment. No treatment or dosage is generated.

Errors preserve the existing format:

```json
{"success":false,"error":{"code":"MODEL_NOT_AVAILABLE","message":"Image classification service is temporarily unavailable."}}
```

Missing/empty/corrupt images return 400, oversized uploads 413, unsupported formats 415,
inference failures 500 and unavailable models 503. Authentication failures return 401.
`GET /health` adds `cattle_image_model: {loaded: boolean, classes: integer}` without paths;
the endpoint's existing database/PostGIS readiness semantics remain intact.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q -p no:cacheprovider
$env:RUN_IMAGE_MODEL_SMOKE = "1"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_cattle_image.py -k optional_real_model -q -rs
```

Normal tests mock the Keras loader and prediction model, not validation/preprocessing. The
optional smoke test uses a generated image to verify real model loading and output structure;
it does not measure accuracy. It skips when not opted in or when artifacts/runtime are absent.
The existing integration suite requires a migrated disposable PostgreSQL/PostGIS `_test` database.

Verification during implementation: 51 unit tests passed and one optional smoke test skipped.
Ruff checks on the new Python modules and `compileall app` passed. TensorFlow 2.21.0 imported
successfully and `pip check` reported no broken requirements. Uvicorn startup succeeded;
live `/docs` and `/openapi.json` returned 200, and the image route returned 401 without a token.
Swagger displayed the new route alongside the existing routes. All four existing integration
tests failed during database fixture setup with PostgreSQL connection timeouts on localhost:5432;
retrying outside the sandbox reproduced the timeout. Database-backed regression behavior could
not be verified in this environment. Real trained-model inference remains unverified because
the `.keras` artifact was not supplied/found.
