from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.core.security import validate_password_policy
from app.core.security import verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.user import ProfileUpdate
from app.schemas.user import UserResponse
from app.services.audit_service import create_audit_log
from app.services.audit_service import model_snapshot


router = APIRouter()

PROFILE_FIELDS = [
    "first_name",
    "last_name",
    "email"
]


@router.get("", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):

    return current_user


@router.put("", response_model=UserResponse)
def update_profile(
    request: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    old_value = model_snapshot(current_user, PROFILE_FIELDS)

    if request.email is not None:
        exists = db.query(User).filter(
            User.email == request.email,
            User.id != current_user.id,
            User.is_deleted == False
        ).first()

        if exists:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

        current_user.email = request.email

    if request.first_name is not None:
        current_user.first_name = request.first_name

    if request.last_name is not None:
        current_user.last_name = request.last_name

    create_audit_log(
        db,
        current_user,
        "profile_update",
        "users",
        current_user.id,
        old_value=old_value,
        new_value=model_snapshot(current_user, PROFILE_FIELDS)
    )

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password")
def change_profile_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not verify_password(
        request.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    validate_password_policy(request.new_password)
    current_user.password_hash = hash_password(request.new_password)

    create_audit_log(
        db,
        current_user,
        "password_change",
        "users",
        current_user.id
    )

    db.commit()

    return {
        "message": "Password changed"
    }
