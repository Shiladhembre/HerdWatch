from fastapi import APIRouter
from app.dependencies import DB, CurrentUser
from app.schemas.auth import RegisterInput, LoginInput, RefreshInput, ForgotInput
from app.schemas.user import UserView
from app.services import auth_service
from app.core.exceptions import DomainError
from app.utils.responses import ok, Envelope

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Envelope[UserView], status_code=201)
async def register(payload: RegisterInput, db: DB):
    """Self-registration creates farmer accounts only. Administrators approve staff roles."""
    return ok(await auth_service.register(db, payload), "Account created")


@router.post("/login", response_model=Envelope[dict])
async def login(payload: LoginInput, db: DB):
    return ok(await auth_service.login(db, payload))


@router.post("/refresh", response_model=Envelope[dict])
async def refresh(payload: RefreshInput, db: DB):
    return ok(await auth_service.refresh(db, payload.refresh_token))


@router.get("/me", response_model=Envelope[UserView])
async def me(user: CurrentUser):
    return ok(UserView.model_validate(user))


@router.post("/logout", response_model=Envelope[dict])
async def logout(payload: RefreshInput, db: DB, user: CurrentUser):
    await auth_service.logout(db, user, payload.refresh_token)
    return ok({"revoked": True})


@router.post("/forgot-password", response_model=Envelope[dict])
async def forgot(payload: ForgotInput):
    raise DomainError(
        "PROVIDER_NOT_CONFIGURED", "Password reset delivery is not configured. Contact an administrator.", 503
    )
