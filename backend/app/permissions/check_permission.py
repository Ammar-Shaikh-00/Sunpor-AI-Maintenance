from fastapi import Depends
from fastapi import HTTPException

from app.core.dependencies import get_current_user


class RequirePermission:

    def __init__(
        self,
        permission_code: str
    ):
        self.permission_code = permission_code

    def __call__(
        self,
        user=Depends(get_current_user)
    ):

        permission_codes = {
            permission.code
            for role in user.roles
            for permission in role.permissions
        }

        if (
            self.permission_code not in permission_codes
            and "system.admin" not in permission_codes
        ):
            raise HTTPException(
                status_code=403,
                detail="Missing required permission"
            )

        return user


def require_permission(permission_code: str):

    def checker(user=Depends(get_current_user)):

        permission_codes = {
            permission.code
            for role in user.roles
            for permission in role.permissions
        }

        if (
            permission_code not in permission_codes
            and "system.admin" not in permission_codes
        ):
            raise HTTPException(
                status_code=403,
                detail="Missing required permission"
            )

        return user

    return checker


def require_any_permission(*permission_codes: str):

    def checker(user=Depends(get_current_user)):
        user_permissions = {
            permission.code
            for role in user.roles
            for permission in role.permissions
        }

        if "system.admin" in user_permissions:
            return user

        if not any(code in user_permissions for code in permission_codes):
            raise HTTPException(
                status_code=403,
                detail="Missing required permission"
            )

        return user

    return checker


def is_super_admin_user(user) -> bool:
    role_names = {role.name for role in (user.roles or [])}
    return "SuperAdmin" in role_names


def require_super_admin():
    """Restrict endpoint to users with the SuperAdmin role."""

    def checker(user=Depends(get_current_user)):
        if not is_super_admin_user(user):
            raise HTTPException(
                status_code=403,
                detail="SuperAdmin role required",
            )
        return user

    return checker


def is_operator_only_user(user) -> bool:
    role_names = {role.name for role in (user.roles or [])}
    return "Operator" in role_names and not role_names.intersection(
        {"Admin", "SuperAdmin"}
    )


def require_operator_only():
    """Restrict endpoint to Operator role users (excludes Admin / SuperAdmin)."""

    def checker(user=Depends(get_current_user)):
        if not is_operator_only_user(user):
            raise HTTPException(
                status_code=403,
                detail="Operator role required",
            )
        return user

    return checker
