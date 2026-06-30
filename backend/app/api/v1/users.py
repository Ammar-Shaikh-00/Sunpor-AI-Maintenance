from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.security import validate_password_policy
from app.db.database import get_db
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.permissions.check_permission import require_permission
from app.schemas.assignment import RoleAssignmentRequest
from app.schemas.role import RoleResponse
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse
from app.schemas.user import UserUpdate
from app.services.audit_service import create_audit_log
from app.services.audit_service import model_snapshot


router = APIRouter()

USER_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "is_active"
]


def get_user_or_404(db: Session, user_id: int):

    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


def ensure_email_available(db: Session, email: str, user_id: int | None = None):

    query = db.query(User).filter(
        User.email == email,
        User.is_deleted == False
    )

    if user_id is not None:
        query = query.filter(User.id != user_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.view"))
):

    return db.query(User).filter(
        User.is_deleted == False
    ).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.view"))
):

    return get_user_or_404(db, user_id)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.create"))
):

    validate_password_policy(request.password)
    ensure_email_available(db, request.email)

    user = User(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        password_hash=hash_password(request.password),
        is_active=request.is_active
    )

    db.add(user)
    db.flush()

    create_audit_log(
        db,
        current_user,
        "user_create",
        "users",
        user.id,
        new_value=model_snapshot(user, USER_FIELDS)
    )

    db.commit()
    db.refresh(user)

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.update"))
):

    user = get_user_or_404(db, user_id)
    old_value = model_snapshot(user, USER_FIELDS)

    if request.email is not None:
        ensure_email_available(db, request.email, user_id=user_id)
        user.email = request.email

    if request.first_name is not None:
        user.first_name = request.first_name

    if request.last_name is not None:
        user.last_name = request.last_name

    if request.is_active is not None:
        user.is_active = request.is_active

    if request.password is not None:
        validate_password_policy(request.password)
        user.password_hash = hash_password(request.password)

    create_audit_log(
        db,
        current_user,
        "user_update",
        "users",
        user.id,
        old_value=old_value,
        new_value=model_snapshot(user, USER_FIELDS)
    )

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.delete"))
):

    user = get_user_or_404(db, user_id)
    old_value = model_snapshot(user, USER_FIELDS)
    user.is_deleted = True
    user.is_active = False

    create_audit_log(
        db,
        current_user,
        "user_delete",
        "users",
        user.id,
        old_value=old_value
    )

    db.commit()

    return {
        "message": "User deleted"
    }


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.update"))
):

    user = get_user_or_404(db, user_id)
    old_value = model_snapshot(user, USER_FIELDS)
    user.is_active = True

    create_audit_log(
        db,
        current_user,
        "user_activate",
        "users",
        user.id,
        old_value=old_value,
        new_value=model_snapshot(user, USER_FIELDS)
    )

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.update"))
):

    user = get_user_or_404(db, user_id)
    old_value = model_snapshot(user, USER_FIELDS)
    user.is_active = False

    create_audit_log(
        db,
        current_user,
        "user_deactivate",
        "users",
        user.id,
        old_value=old_value,
        new_value=model_snapshot(user, USER_FIELDS)
    )

    db.commit()
    db.refresh(user)

    return user


@router.get("/{user_id}/roles", response_model=list[RoleResponse])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.assign"))
):

    user = get_user_or_404(db, user_id)

    return user.roles


@router.post("/{user_id}/roles", response_model=list[RoleResponse])
def assign_user_roles(
    user_id: int,
    request: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.assign"))
):

    user = get_user_or_404(db, user_id)

    roles = db.query(Role).filter(
        Role.id.in_(request.role_ids)
    ).all()

    if len(roles) != len(set(request.role_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more roles were not found"
        )

    for role in roles:
        exists = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id
        ).first()

        if not exists:
            db.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id
                )
            )

    create_audit_log(
        db,
        current_user,
        "role_assign",
        "user_roles",
        user.id,
        new_value={"role_ids": request.role_ids}
    )

    db.commit()
    db.refresh(user)

    return user.roles


@router.delete("/{user_id}/roles/{role_id}")
def remove_user_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.assign"))
):

    user = get_user_or_404(db, user_id)
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role_id
    ).first()

    if not user_role:
        raise HTTPException(
            status_code=404,
            detail="User role not found"
        )

    db.delete(user_role)
    create_audit_log(
        db,
        current_user,
        "role_remove",
        "user_roles",
        user.id,
        old_value={"role_id": role_id}
    )

    db.commit()

    return {
        "message": "Role removed from user"
    }
