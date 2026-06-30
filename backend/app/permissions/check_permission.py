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
