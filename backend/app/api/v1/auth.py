from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.auth import LoginRequest
from app.schemas.auth import TokenResponse
from app.schemas.auth import ChangePasswordRequest
from app.schemas.auth import ResetPasswordRequest
from app.schemas.user import UserResponse

from app.services.auth_service import authenticate_user
from app.services.audit_service import create_audit_log

from app.core.security import create_access_token
from app.core.security import hash_password
from app.core.security import validate_password_policy
from app.core.security import verify_password
from app.core.dependencies import get_current_user
from app.permissions.check_permission import require_permission
from app.models.user import User


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db,
        request.email,
        request.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": str(user.id)
        }
    )

    create_audit_log(
        db,
        user,
        "login",
        "users",
        user.id
    )
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    current_user: User = Depends(get_current_user)
):

    token = create_access_token(
        {
            "sub": str(current_user.id)
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    create_audit_log(
        db,
        current_user,
        "logout",
        "users",
        current_user.id
    )
    db.commit()

    return {
        "message": "Logged out"
    }


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user)
):

    return current_user


@router.post("/change-password")
def change_password(
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


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.update"))
):

    validate_password_policy(request.new_password)

    user = db.query(User).filter(
        User.email == request.email,
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password_hash = hash_password(request.new_password)
    create_audit_log(
        db,
        current_user,
        "password_reset",
        "users",
        user.id
    )
    db.commit()

    return {
        "message": "Password reset"
    }
