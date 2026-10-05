# 🐄 HerdWatch — AI-Powered Livestock Disease Surveillance & Early Warning Platform

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791?logo=postgresql)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?logo=tensorflow)

**HerdWatch** is a full-stack, enterprise-grade animal health surveillance platform designed for farmers, field workers, veterinarians, and district agricultural officers. It combines deep learning image screening, symptom-based differential diagnosis, geospatial PostGIS outbreak mapping, and environmental risk tracking into a unified early-warning system.

---

## 📌 Key Features

- **📸 Computer Vision Cattle Screening**: Real-time screening of cattle lesions and skin conditions using a fine-tuned MobileNetV2 deep learning model (`Foot-and-Mouth Disease`, `Lumpy Skin Disease`, `Healthy`).
- **🩺 Symptom-Based Differential Predictor**: 18-factor diagnostic screening model predicting 6 critical livestock conditions (`Antraks`, `FMD`, `Leptospirosis`, `Mastitis`, `Piroplasmosis`, `Surra`).
- **🗺️ GIS Outbreak Mapping**: Interactive Leaflet maps backed by PostgreSQL/PostGIS spatial queries to track disease clusters and quarantine boundaries in real time.
- **🌤️ Environmental Risk Modeling**: Integration with meteorological datasets (e.g., NASA POWER API) to assess outbreak vulnerability from temperature, humidity, and rainfall patterns.
- **👥 Role-Based Access Control (RBAC)**: Fine-grained workflows for 5 stakeholder roles:
  - `FARMER`: Animal registry, case reporting, image & symptom screening.
  - `FIELD_WORKER`: Field triage, sample collection, rapid reporting.
  - `VETERINARIAN`: Clinical verification, lab diagnostics, treatment orders.
  - `DISTRICT_OFFICER`: Regional surveillance, quarantine zone enforcement, analytics.
  - `ADMIN`: User management, audit logs, model registry, system settings.
- **💉 Animal & Herd Lifecycle Management**: Records for livestock inventory, vaccination schedules, lab tests, and disease timelines.
- **⚡ Offline-Friendly & Demo Mode**: Frontend toggleable demo mode (`VITE_DEMO_MODE=true`) allows exploring UI workflows without live database dependencies.

---

## 🏛️ System Architecture

```text
livestock-disease-project/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints (auth, animals, cases, predict, etc.)
│   │   ├── core/                # Security, middleware, logging, upload boundaries
│   │   ├── ml/                  # Symptom classifier loader and registry
│   │   ├── models/              # SQLAlchemy ORM models (19 relational tables)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic, image classifier, cache, NASA weather
│   │   ├── database.py          # Async SQLAlchemy engine with PostgreSQL/PostGIS
│   │   ├── main.py              # FastAPI application entry & lifecycle
│   │   └── server.py            # Windows asyncio Selector loop entry point
│   ├── alembic/                 # Database migrations (0001_initial)
│   ├── models/                  # ML model artifacts (.pkl, .keras, metadata)
│   │   └── cattle_image/        # MobileNetV2 .keras model and class labels
│   ├── tests/                   # Pytest unit & integration test suites
│   ├── docker-compose.yml       # PostgreSQL/PostGIS & Redis services
│   ├── requirements.txt         # Python dependencies
│   └── STARTUP.md               # Backend operational notes
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components & screening forms
│   │   ├── context/             # AuthContext, LanguageContext, AppContext
│   │   ├── pages/               # Dashboard, OutbreakMap, SymptomChecker, Animals, etc.
│   │   ├── services/            # Axios API client & error handling
│   │   └── App.jsx              # Routing & role-based permission guards
│   ├── package.json             # React 19, Vite, Tailwind CSS v4, Leaflet
│   └── vite.config.js
│
├── data/
│   └── Cows datasets/           # Image datasets (foot-and-mouth, healthy, lumpy)
├── train_cow_model.py           # Deep learning model training pipeline
└── QA_TEST_REPORT.md            # Verified quality assurance test audit
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python** 3.11+ (virtual environment configured in `backend/.venv`)
- **Node.js** 18+ & **npm**
- **Docker & Docker Compose** *(or a local PostgreSQL 16+ instance with PostGIS)*

---

### 1. Database Setup (PostgreSQL + PostGIS)

#### Option A: Using Docker (Recommended)
```powershell
cd backend
docker compose up -d postgres
```
*(To include Redis caching, run: `docker compose up -d postgres redis`)*

#### Option B: Local PostgreSQL Installation
If Docker is not installed on your system:
1. Install [PostgreSQL](https://www.postgresql.org/download/) and install the **PostGIS** extension via Stack Builder.
2. Create a database named `livestock_db` and user `livestock` with credentials matching `backend/.env`.
3. In PostgreSQL, enable PostGIS:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

---

### 2. Backend Setup & Startup

From the `backend` directory:

```powershell
cd backend

# 1. Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Or on Linux/macOS: source .venv/bin/activate

# 2. Run database migrations to create all 19 application tables
python -m alembic upgrade head

# 3. Start the FastAPI server
# On Windows, use app.server to ensure SelectorEventLoop compatibility with psycopg:
python -m app.server

# On Linux / macOS:
# uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- **API Base URL**: `http://127.0.0.1:8000/api/v1`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **System Health Check**: `http://127.0.0.1:8000/health`

---

### 3. Frontend Setup & Startup

Open a second terminal window:

```powershell
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```

- **Frontend Application**: `http://localhost:5173`

---

## ⚙️ Environment Configuration

### Backend Configuration (`backend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development` / `production`) |
| `DATABASE_URL` | `postgresql+psycopg://...` | Connection URI with async `psycopg` driver |
| `JWT_SECRET_KEY` | *(64-char key)* | Secret key for signing authentication tokens |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `IMAGE_MODEL_PATH` | `models/cattle_image/...` | Path to trained `.keras` MobileNetV2 artifact |
| `IMAGE_CLASSES_PATH` | `models/cattle_image/...` | Path to class labels JSON |
| `IMAGE_MODEL_CONFIDENCE_THRESHOLD` | `0.70` | Threshold below which low confidence warning triggers |
| `IMAGE_MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Maximum permitted image upload size |
| `SYMPTOM_MODEL_PATH` | `models/...pkl` | Scikit-learn symptom classification model |

### Frontend Configuration (`frontend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Target FastAPI backend URL |
| `VITE_DEMO_MODE` | `true` | When `true`, enables mock data and offline UI exploration. Set `false` for live backend API. |

---

## 🧠 Machine Learning Models

### 1. Cattle Disease Image Classifier (Keras / MobileNetV2)
- **Input**: RGB Images (JPEG, PNG, WebP), preprocessed to `224x224x3`.
- **Target Classes**:
  1. `foot-and-mouth` (Foot-and-Mouth Disease)
  2. `healthy` (No visible lesions)
  3. `lumpy` (Lumpy Skin Disease)
- **Artifact**: `backend/models/cattle_image/cattle_disease_image_model.keras`
- **Training Pipeline**: To retrain or fine-tune with new imagery, run:
  ```powershell
  python train_cow_model.py
  ```

### 2. Symptom Disease Predictor (Scikit-Learn)
- **Input**: 18 binary/graded symptom indicators (fever, mouth lesions, lameness, milk drop, etc.).
- **Target Diseases**: `Antraks`, `FMD`, `Leptospirosis`, `Mastitis`, `Piroplasmosis`, `Surra`.
- **Artifacts**:
  - `backend/models/livestock_disease_model.pkl`
  - `backend/models/disease_label_encoder.pkl`
  - `backend/models/model_metadata.json`

> [!NOTE]
> All AI screening results display clear disclaimers that predictions are screening aids and must be validated by a licensed veterinarian. The system does not automatically prescribe medication.

---

## 🧪 Testing

### Backend Unit Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/unit -v -p no:cacheprovider
```

### Optional Image Model Smoke Test
```powershell
cd backend
$env:RUN_IMAGE_MODEL_SMOKE = "1"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_cattle_image.py -k optional_real_model -v
```

### Frontend Tests & Linting
```powershell
cd frontend
npm test
npm run lint
npm run build
```

---

## 🛠️ Common Troubleshooting

### 1. `docker: The term 'docker' is not recognized`
If Docker Desktop is not installed on your machine:
- Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/), start it, and run `docker compose up -d postgres`.
- **Alternative**: Run a local PostgreSQL service with the PostGIS extension installed and ensure the port is `5432` with matching credentials in `backend/.env`.
- **Alternative (UI Exploration)**: Keep `VITE_DEMO_MODE=true` in `frontend/.env` to navigate and test all frontend views without a running database.

### 2. Windows Async Loop / psycopg Error
If you encounter `NotImplementedError` or event-loop crashes on Windows when running Uvicorn:
- Ensure you start the backend with `python -m app.server` (not raw `uvicorn app.main:app`). `app/server.py` forces Python to use `asyncio.SelectorEventLoop`, which `psycopg` requires on Windows.

### 3. Image Upload Returns 401
- `/api/v1/predict/image` is an authenticated endpoint. First login via `POST /api/v1/auth/login` (or in Swagger `/docs` using the **Authorize** button with the Bearer token) before sending prediction requests.

---

## 📄 License
Internal proprietary research & surveillance project. All rights reserved.
#   H e r d W a t c h  
 