import io
from pathlib import Path
from uuid import uuid4
from asyncio import to_thread
from PIL import Image, UnidentifiedImageError
from app.config import get_settings
from app.models import Attachment, Case
from app.core.constants import Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError
from app.repositories.base import get_scoped
from .audit_service import audit


class LocalAttachmentStore:
    def put(self, key, content):
        root = get_settings().upload_dir.resolve()
        root.mkdir(parents=True, exist_ok=True)
        target = (root / key).resolve()
        if target.parent != root:
            raise DomainError("INVALID_PATH", "Invalid storage key.", 422)
        with target.open("xb") as file:
            file.write(content)
        return target


store = LocalAttachmentStore()


async def upload(db, user, id, file):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    await get_scoped(db, Case, id, user)
    extension = Path(file.filename or "").suffix.lower()
    allowed = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    if allowed.get(extension) != file.content_type:
        raise DomainError("INVALID_UPLOAD_TYPE", "Use JPEG, PNG, WebP or PDF with matching MIME type.", 422)
    content = await file.read(get_settings().max_upload_bytes + 1)
    if len(content) > get_settings().max_upload_bytes:
        raise DomainError("UPLOAD_TOO_LARGE", "File exceeds the configured upload limit.", 413)
    if not content:
        raise DomainError("EMPTY_UPLOAD", "Empty files are not accepted.", 422)
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise DomainError("INVALID_UPLOAD", "Invalid PDF signature.", 422)
    else:
        try:
            with Image.open(io.BytesIO(content)) as image:
                if image.width * image.height > 25_000_000:
                    raise ValueError("Image too large")
                expected = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[extension]
                if image.format != expected:
                    raise ValueError("Image format mismatch")
                image.verify()
            # Re-encode images to remove metadata and embedded payloads.
            with Image.open(io.BytesIO(content)) as image:
                target = io.BytesIO()
                image.convert("RGB").save(target, format="JPEG", quality=90)
                content = target.getvalue()
            extension = ".jpg"
            mime = "image/jpeg"
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise DomainError("INVALID_UPLOAD", "Invalid or oversized image.", 422) from None
    if extension == ".pdf":
        mime = "application/pdf"
    key = f"{uuid4().hex}{extension}"
    path = await to_thread(store.put, key, content)
    try:
        row = Attachment(case_id=id, uploaded_by=user.id, storage_key=key, content_type=mime, size_bytes=len(content))
        db.add(row)
        await db.flush()
        audit(db, user, "attachment_uploaded", row)
        return row
    except Exception:
        path.unlink(missing_ok=True)
        raise
