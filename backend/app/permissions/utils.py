from app.models.user import User


def get_user_permission_codes(user: User) -> set[str]:
    return {
        permission.code
        for role in user.roles
        for permission in role.permissions
    }
