import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.config import get_settings
from app.database import engine
from app.api.router import router
from app.api.routes.health import router as health_router
from app.ml.model_loader import registry
from app.services.cache import cache
from app.core.exceptions import DomainError
from app.core.middleware import RequestMiddleware
from app.core.logging import log_event
from app.services.cattle_image_classifier import classifier
from app.core.image_upload_middleware import ImageUploadLimitMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(registry.load)
    await asyncio.to_thread(classifier.load)
    try:
        await cache.connect()
    except Exception:
        if settings.app_env == "production":
            raise
        cache.redis = None
        log_event("cache_unavailable", fallback="bounded_process_cache")
    yield
    await cache.close()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Animal-health surveillance with human veterinary confirmation. Missing model artifacts never produce simulated predictions.",
    lifespan=lifespan,
    debug=False,
)
app.add_middleware(RequestMiddleware)
app.add_middleware(ImageUploadLimitMiddleware, path=settings.api_v1_prefix + "/predict/image",
                   max_bytes=settings.image_max_upload_bytes + 65_536)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[s.strip() for s in settings.frontend_url.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    expose_headers=["X-Request-ID"],
)
app.include_router(router, prefix=settings.api_v1_prefix)
app.include_router(health_router)


@app.exception_handler(DomainError)
async def domain_error(request: Request, error: DomainError):
    return JSONResponse(
        {"success": False, "error": {"code": error.code, "message": error.message}},
        error.status,
        headers={"WWW-Authenticate": "Bearer"} if error.status == 401 else {},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    details = [{"location": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in error.errors()]
    return JSONResponse(
        {
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": details},
        },
        422,
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException):
    return JSONResponse(
        {"success": False, "error": {"code": f"HTTP_{error.status_code}", "message": str(error.detail)}},
        error.status_code,
    )


@app.exception_handler(IntegrityError)
async def conflict(request: Request, error: IntegrityError):
    return JSONResponse(
        {
            "success": False,
            "error": {
                "code": "DATA_CONFLICT",
                "message": "The operation conflicts with an existing or referenced record.",
            },
        },
        409,
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, error: SQLAlchemyError):
    log_event("database_error", request_id=getattr(request.state, "request_id", None), error_type=type(error).__name__)
    return JSONResponse(
        {
            "success": False,
            "error": {"code": "DATABASE_UNAVAILABLE", "message": "The database operation could not be completed."},
        },
        503,
    )
