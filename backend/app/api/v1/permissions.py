from app.api.v1.crud_utils import register_crud_routes
from app.models.permission import Permission
from app.permissions.check_permission import require_permission
from app.schemas.permission import PermissionCreate
from app.schemas.permission import PermissionResponse
from app.schemas.permission import PermissionUpdate
from fastapi import APIRouter


router = APIRouter()

register_crud_routes(
    router,
    Permission,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    require_permission("system.admin"),
    "permission"
)
