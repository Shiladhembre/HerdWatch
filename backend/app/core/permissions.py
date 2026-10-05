from sqlalchemy import and_
from app.core.constants import Role
from app.core.exceptions import PermissionDenied


def require_role(user, *roles):
    if user.role != Role.ADMIN and user.role not in roles:
        raise PermissionDenied()


def district_allowed(user, district):
    if user.role != Role.ADMIN and user.district.casefold() != district.casefold():
        raise PermissionDenied()


def scope(model, user, owner_column="owner_id"):
    if user.role == Role.ADMIN:
        return True
    district = model.district == user.district
    if user.role == Role.FARMER:
        return and_(district, getattr(model, owner_column) == user.id)
    return district


def check_record(record, user, owner_column="owner_id"):
    district_allowed(user, record.district)
    if user.role == Role.FARMER and getattr(record, owner_column) != user.id:
        raise PermissionDenied()
