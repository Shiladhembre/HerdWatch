"""Independent cattle image screening; never combines symptom probabilities."""
import io
import json
import threading
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.core.exceptions import DomainError, ModelUnavailable
from app.core.logging import logger, log_event

CLASSES = ("foot-and-mouth", "healthy", "lumpy")
DISPLAY_NAMES = dict(zip(CLASSES, ("Foot-and-Mouth Disease (FMD)", "Healthy", "Lumpy Skin Disease (LSD)")))
BACKEND_ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = (
    "This result is an AI-assisted screening result and is not a veterinary diagnosis. "
    "Consult a qualified veterinarian for confirmation. Model confidence is not diagnostic certainty."
)


def resolve_artifact(path):
    path = Path(path)
    return path if path.is_absolute() else BACKEND_ROOT / path


def load_keras_model(path):
    import tensorflow as tf
    try:
        return tf.keras.models.load_model(path, compile=False, safe_mode=True)
    except Exception:
        return tf.keras.models.load_model(path, compile=False, safe_mode=False)


class CattleImageClassifier:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._model = None
        self._classes = ()
        self._attempted = False
        self._load_lock = threading.Lock()
        self._predict_lock = threading.Lock()

    @property
    def status(self):
        return {"loaded": self._model is not None, "classes": len(self._classes)}

    def load(self):
        # One attempt per worker, including failures; restart after fixing artifacts.
        with self._load_lock:
            if self._attempted:
                return
            self._attempted = True
            try:
                path = resolve_artifact(self.settings.image_model_path)
                metadata = json.loads(resolve_artifact(self.settings.image_classes_path).read_text(encoding="utf-8"))
                classes = metadata["classes"]
                if len(classes) != 3 or set(classes) != set(CLASSES):
                    raise ValueError("Expected exactly Healthy/FMD/Lumpy classes")
                if metadata.get("class_to_index") != {name: i for i, name in enumerate(classes)}:
                    raise ValueError("Class index mapping is inconsistent")
                if metadata.get("image_size") != [224, 224]:
                    raise ValueError("Expected 224x224 input")
                if not path.is_file():
                    raise FileNotFoundError("Cattle image model artifact is missing")
                model = load_keras_model(path)
                if tuple(model.input_shape) != (None, 224, 224, 3) or tuple(model.output_shape) != (None, 3):
                    raise ValueError("Unexpected image model input/output shape")
                self._classes = tuple(classes)
                self._model_name = metadata.get("model", "MobileNetV2") + " Cattle Disease Image Classifier"
                self._model = model
                log_event("cattle_image_model_loaded", classes=3)
            except Exception:
                logger.exception("Cattle image model unavailable; fix artifacts/runtime and restart the worker")

    def preprocess(self, image_bytes):
        if not image_bytes:
            raise DomainError("EMPTY_IMAGE", "The uploaded image is empty.", 400)
        if len(image_bytes) > self.settings.image_max_upload_bytes:
            raise DomainError("IMAGE_TOO_LARGE", "Image exceeds the maximum allowed upload size.", 413)
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise DomainError("UNSUPPORTED_IMAGE", "Unsupported image type.", 415)
                if image.width * image.height > self.settings.image_max_pixels:
                    raise ValueError("Decoded image exceeds pixel limit")
                image.verify()
            with Image.open(io.BytesIO(image_bytes)) as image:
                # Matches keras.utils.load_img's default nearest interpolation.
                # EfficientNet includes rescaling: retain float32 pixels in [0, 255].
                image = image.convert("RGB").resize((224, 224), Image.Resampling.NEAREST)
                return np.asarray(image, dtype=np.float32)[None, ...]
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
            log_event("invalid_cattle_image", error_type=type(exc).__name__)
            raise DomainError("INVALID_IMAGE", "The uploaded file is not a valid image.", 400) from exc

    def predict(self, image_bytes: bytes) -> dict:
        batch = self.preprocess(image_bytes)
        self.load()
        if self._model is None:
            raise ModelUnavailable("Image classification service is temporarily unavailable.")
        try:
            with self._predict_lock:
                output = np.asarray(self._model.predict(batch, verbose=0), dtype=np.float64)
            if (output.shape != (1, 3) or not np.isfinite(output).all()
                    or (output < 0).any() or (output > 1).any()
                    or not np.isclose(output.sum(), 1.0, atol=1e-4)):
                raise ValueError("Model returned invalid probabilities")
            values = output[0]
            index = int(np.argmax(values))
            label = self._classes[index]
            confidence = float(values[index])
            low = confidence < self.settings.image_model_confidence_threshold
            return {
                "success": True,
                "prediction": {"class": label, "display_name": DISPLAY_NAMES[label],
                               "confidence": confidence, "confidence_percent": round(confidence * 100, 2),
                               "low_confidence": low},
                "probabilities": dict(zip(self._classes, map(float, values))),
                "model": {"name": getattr(self, "_model_name", "MobileNetV2 Cattle Disease Image Classifier"), "classes": list(self._classes)},
                "message": ("The image result is uncertain; veterinary assessment is recommended." if low
                            else "AI-assisted cattle image screening completed. Veterinary confirmation recommended."),
                "disclaimer": DISCLAIMER,
            }
        except Exception as exc:
            logger.exception("Cattle image prediction failed")
            raise DomainError("IMAGE_PREDICTION_FAILED", "Image prediction could not be completed.", 500) from exc


classifier = CattleImageClassifier()


def get_image_classifier():
    return classifier
