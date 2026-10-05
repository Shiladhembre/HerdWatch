from sqlalchemy import inspect
from fastapi.encoders import jsonable_encoder

EXCLUDED = {"password_hash", "geom", "request_hash", "refresh_jti", "storage_key"}


def record(obj, exclude=()):
    return jsonable_encoder(
        {
            col.key: getattr(obj, col.key)
            for col in inspect(obj).mapper.column_attrs
            if col.key not in EXCLUDED and col.key not in exclude
        }
    )


def page(result):
    return {**result, "items": [record(x) for x in result["items"]]}
