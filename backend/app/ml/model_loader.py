import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
import joblib
from app.config import get_settings
from app.core.logging import log_event
from app.core.symptom_config import FEATURE_CODES
from .metadata import ModelContract
from .feature_validation import LEAKAGE_FIELDS


@dataclass
class ModelSlot:
    model: object = None
    contract: ModelContract | None = None
    status: str = "not_configured"
    error_code: str | None = None
    encoder: object = None


def artifact_path(path):
    path = Path(path)
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


class ModelRegistry:
    def __init__(self):
        self.symptom = ModelSlot()
        self.outbreak = ModelSlot()

    def load(self):
        settings = get_settings()
        try:
            metadata = json.loads(artifact_path(settings.model_metadata_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            metadata = {}
        for name, path in [("symptom", settings.symptom_model_path), ("outbreak", settings.outbreak_model_path)]:
            path = artifact_path(path)
            slot = ModelSlot()
            setattr(self, name, slot)
            if not path.exists():
                continue
            if not settings.trust_model_artifacts:
                slot.status = "untrusted_artifact"
                slot.error_code = "MODEL_NOT_AVAILABLE"
                continue
            try:
                contract = ModelContract.model_validate(metadata.get(f"{name}_model", {}))
                if (
                    not contract.verified
                    or not contract.features
                    or len(set(contract.features)) != len(contract.features)
                ):
                    raise ValueError("Unverified feature contract")
                if not contract.sha256 or hashlib.sha256(path.read_bytes()).hexdigest() != contract.sha256:
                    raise ValueError("Artifact checksum mismatch")
                if name == "symptom":
                    if set(contract.features) != set(FEATURE_CODES) or len(contract.features) != 18:
                        raise ValueError("Symptom feature mismatch")
                    if contract.label_encoder_sha256:
                        encoder_path = artifact_path(settings.symptom_label_encoder_path)
                        if hashlib.sha256(encoder_path.read_bytes()).hexdigest() != contract.label_encoder_sha256:
                            raise ValueError("Encoder checksum mismatch")
                        slot.encoder = joblib.load(encoder_path)
                        if list(slot.encoder.classes_) != contract.classes:
                            raise ValueError("Encoder class mismatch")
                    else:
                        feature_path = artifact_path(settings.symptom_features_path)
                        if (not contract.feature_artifact_sha256
                                or hashlib.sha256(feature_path.read_bytes()).hexdigest() != contract.feature_artifact_sha256):
                            raise ValueError("Feature checksum mismatch")
                        saved = list(joblib.load(feature_path))
                        if saved != contract.features:
                            raise ValueError("Feature order mismatch")
                else:
                    if set(contract.features) != set(contract.pre_outbreak_features) or any(
                        f.lower() in LEAKAGE_FIELDS for f in contract.features
                    ):
                        raise ValueError("Invalid future risk feature contract")
                if contract.sklearn_version:
                    from sklearn import __version__
                    if __version__ != contract.sklearn_version:
                        raise ValueError("Install the artifact's recorded scikit-learn version")
                model = joblib.load(path)
                if not callable(getattr(model, "predict", None)):
                    raise ValueError("Artifact does not support inference")
                if getattr(model, "n_features_in_", len(contract.features)) != len(contract.features):
                    raise ValueError("Feature count mismatch")
                if hasattr(model, "feature_names_in_") and list(model.feature_names_in_) != contract.features:
                    raise ValueError("Feature order mismatch")
                if slot.encoder is not None and not hasattr(model, "feature_names_in_"):
                    raise ValueError("Encoded model must supply verified feature order")
                if hasattr(model, "classes_"):
                    classes = slot.encoder.inverse_transform(model.classes_) if slot.encoder is not None else model.classes_
                    if set(map(str, classes)) != set(contract.classes):
                        raise ValueError("Class metadata mismatch")
                slot.model = model
                slot.contract = contract
                slot.status = "loaded"
                log_event("model_loaded", model=name, classes=len(contract.classes))
            except Exception as exc:
                slot.status = "invalid_artifact"
                slot.error_code = "MODEL_FEATURE_MISMATCH"
                log_event("model_unavailable", model=name, error_type=type(exc).__name__)


registry = ModelRegistry()
