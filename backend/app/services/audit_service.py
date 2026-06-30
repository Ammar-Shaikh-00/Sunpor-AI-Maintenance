import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_log(
    db: Session,
    user: User,
    action: str,
    table_name: str,
    record_id: str | int,
    old_value=None,
    new_value=None
):

    log = AuditLog(
        user_id=user.id,
        action=action,
        table_name=table_name,
        record_id=str(record_id),
        old_value=json.dumps(old_value) if old_value is not None else None,
        new_value=json.dumps(new_value) if new_value is not None else None
    )

    db.add(log)


def model_snapshot(model, fields: list[str]):

    return {
        field: getattr(model, field)
        for field in fields
    }
