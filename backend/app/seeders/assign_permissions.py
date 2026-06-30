from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.seeders.utils import link_if_missing


def assign_permissions(db: Session) -> dict[str, int]:

    role = db.query(Role).filter(
        Role.name == "SuperAdmin"
    ).first()

    if not role:
        db.commit()
        return {"role_permissions_created": 0}

    created = 0
    permissions = db.query(Permission).all()

    for permission in permissions:
        if link_if_missing(
            db,
            RolePermission,
            lookup={
                "role_id": role.id,
                "permission_id": permission.id,
            },
        ):
            created += 1

    db.commit()

    return {"role_permissions_created": created}
