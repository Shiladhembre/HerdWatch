from functools import lru_cache
from pathlib import Path
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_name: str = "Livestock Disease Surveillance API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(30, ge=1, le=60)
    refresh_token_expire_days: int = Field(7, ge=1, le=30)
    frontend_url: str = "http://localhost:5173"
    nasa_power_base_url: str = "https://power.larc.nasa.gov"
    symptom_model_path: Path = Path("models/symptom_disease_model.pkl")
    symptom_features_path: Path = Path("models/symptom_feature_columns.pkl")
    symptom_label_encoder_path: Path = Path("models/disease_label_encoder.pkl")
    outbreak_model_path: Path = Path("models/outbreak_risk_model.pkl")
    model_metadata_path: Path = Path("models/model_metadata.json")
    upload_dir: Path = Path("uploads")
    redis_url: str | None = None
    enable_model_confidence: bool = False
    trust_model_artifacts: bool = False
    allow_demo_seed: bool = False
    max_upload_bytes: int = Field(5_242_880, ge=1024, le=20_971_520)
    image_model_path: Path = Path("models/cattle_image/cattle_disease_image_model.keras")
    image_classes_path: Path = Path("models/cattle_image/cattle_disease_classes.json")
    image_max_upload_bytes: int = Field(10_485_760, ge=1024, le=20_971_520)
    image_max_pixels: int = Field(20_000_000, ge=50176, le=40_000_000)
    image_model_confidence_threshold: float = Field(0.70, ge=0, le=1)

    @model_validator(mode="after")
    def secure_configuration(self):
        secret = self.jwt_secret_key.get_secret_value()
        if len(secret) < 32 or "CHANGE_ME" in secret:
            raise ValueError("Set a randomly generated JWT_SECRET_KEY with at least 32 characters.")
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL with the psycopg driver.")
        if self.jwt_algorithm != "HS256":
            raise ValueError("This deployment supports HS256 only.")
        if "*" in self.frontend_url:
            raise ValueError("Explicit FRONTEND_URL origins are required.")
        if self.nasa_power_base_url != "https://power.larc.nasa.gov":
            raise ValueError("Weather upstream must be the official NASA POWER origin.")
        if self.app_env == "production" and (
            self.debug or not self.frontend_url.startswith("https://") or self.allow_demo_seed
        ):
            raise ValueError("Production requires HTTPS, debug disabled and demo seeding disabled.")
        return self


@lru_cache
def get_settings():
    return Settings()
