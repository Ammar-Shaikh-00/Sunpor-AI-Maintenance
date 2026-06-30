from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.permissions.check_permission import require_permission
from app.schemas.permission import PermissionAssignmentRequest
from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleCreate
from app.schemas.role import RoleResponse
from app.schemas.role import RoleUpdate
from app.services.audit_service import create_audit_log
from app.services.audit_service import model_snapshot


router = APIRouter()

ROLE_FIELDS = [
    "name",
    "description"
]


def get_role_or_404(db: Session, role_id: int):

    role = db.query(Role).filter(
        Role.id == role_id
    ).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    return role


def ensure_role_name_available(
    db: Session,
    name: str,
    role_id: int | None = None
):

    query = db.query(Role).filter(
        Role.name == name
    )

    if role_id is not None:
        query = query.filter(Role.id != role_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Role name already exists"
        )


@router.get("", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):

    return db.query(Role).order_by(Role.id).all()


@router.post("", response_model=RoleResponse, status_code=201)
def create_role(
    request: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.create"))
):

    ensure_role_name_available(db, request.name)

    role = Role(
        name=request.name,
        description=request.description
    )

    db.add(role)
    db.flush()

    create_audit_log(
        db,
        current_user,
        "role_create",
        "roles",
        role.id,
        new_value=model_snapshot(role, ROLE_FIELDS)
    )

    db.commit()
    db.refresh(role)

    return role


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):

    return get_role_or_404(db, role_id)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.update"))
):

    role = get_role_or_404(db, role_id)
    old_value = model_snapshot(role, ROLE_FIELDS)

    if request.name is not None:
        ensure_role_name_available(db, request.name, role_id=role_id)
        role.name = request.name

    if request.description is not None:
        role.description = request.description

    create_audit_log(
        db,
        current_user,
        "role_update",
        "roles",
        role.id,
        old_value=old_value,
        new_value=model_snapshot(role, ROLE_FIELDS)
    )

    db.commit()
    db.refresh(role)

    return role


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.delete"))
):

    role = get_role_or_404(db, role_id)
    old_value = model_snapshot(role, ROLE_FIELDS)

    if role.name == "SuperAdmin":
        raise HTTPException(
            status_code=400,
            detail="SuperAdmin role cannot be deleted"
        )

    create_audit_log(
        db,
        current_user,
        "role_delete",
        "roles",
        role.id,
        old_value=old_value
    )

    db.query(UserRole).filter(
        UserRole.role_id == role.id
    ).delete()

    db.query(RolePermission).filter(
        RolePermission.role_id == role.id
    ).delete()

    db.delete(role)
    db.commit()

    return {
        "message": "Role deleted"
    }


@router.get("/{role_id}/permissions", response_model=list[PermissionResponse])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.view"))
):

    role = get_role_or_404(db, role_id)

    return role.permissions


@router.post("/{role_id}/permissions", response_model=list[PermissionResponse])
def assign_role_permissions(
    role_id: int,
    request: PermissionAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.update"))
):

    role = get_role_or_404(db, role_id)
    permissions = db.query(Permission).filter(
        Permission.id.in_(request.permission_ids)
    ).all()

    if len(permissions) != len(set(request.permission_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more permissions were not found"
        )

    for permission in permissions:
        exists = db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id
        ).first()

        if not exists:
            db.add(
                RolePermission(
                    role_id=role.id,
                    permission_id=permission.id
                )
            )

    create_audit_log(
        db,
        current_user,
        "permission_assign",
        "role_permissions",
        role.id,
        new_value={"permission_ids": request.permission_ids}
    )

    db.commit()
    db.refresh(role)

    return role.permissions


@router.delete("/{role_id}/permissions/{permission_id}")
def remove_role_permission(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.update"))
):

    role = get_role_or_404(db, role_id)
    role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role.id,
        RolePermission.permission_id == permission_id
    ).first()

    if not role_permission:
        raise HTTPException(
            status_code=404,
            detail="Role permission not found"
        )

    db.delete(role_permission)
    create_audit_log(
        db,
        current_user,
        "permission_remove",
        "role_permissions",
        role.id,
        old_value={"permission_id": permission_id}
    )

    db.commit()

    return {
        "message": "Permission removed from role"
    }
