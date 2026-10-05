from app.models import AuditLog


def audit(db, user, action, entity, details=None):
    db.add(
        AuditLog(
            user_id=user.id, action=action, entity_type=entity.__tablename__, entity_id=entity.id, details=details or {}
        )
    )
