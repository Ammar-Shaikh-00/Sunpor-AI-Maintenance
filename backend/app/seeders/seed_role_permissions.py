from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.seeders.utils import link_if_missing


ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "Admin": [
        "user.create",
        "user.view",
        "user.update",
        "user.delete",
        "role.create",
        "role.view",
        "role.update",
        "role.delete",
        "role.assign",
        "production.view",
        "production.create",
        "production.update",
        "event.view",
        "event.create",
        "quality.view",
        "quality.create",
        "material_block.view",
        "material_block.create",
        "signal.view",
    ],
    "Operator": [
        "production.view",
        "production.create",
        "event.view",
        "event.create",
        "quality.view",
        "quality.create",
        "material_block.view",
        "material_block.create",
    ],
    "ProductionManager": [
        "production.view",
        "production.create",
        "production.update",
        "event.view",
        "event.create",
        "event.update",
        "quality.view",
        "quality.create",
        "quality.update",
        "material_block.view",
        "material_block.create",
    ],
    "QA": [
        "quality.view",
        "quality.create",
        "quality.update",
        "material_block.view",
        "material_block.create",
        "production.view",
    ],
}


def seed_role_permissions(db: Session) -> dict[str, int]:
    created = 0

    for role_name, permission_codes in ROLE_PERMISSION_MAP.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            continue

        for code in permission_codes:
            permission = db.query(Permission).filter(
                Permission.code == code
            ).first()
            if not permission:
                continue

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
