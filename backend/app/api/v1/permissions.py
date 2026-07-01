from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.v1.crud_utils import register_crud_routes
from app.db.database import get_db
from app.models.permission import Permission
from app.permissions.check_permission import require_permission
from app.schemas.permission import PermissionCreate
from app.schemas.permission import PermissionResponse
from app.schemas.permission import PermissionUpdate


router = APIRouter()


@router.get("/catalog", response_model=list[PermissionResponse])
def list_permission_catalog(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("role.view")),
):

    return db.query(Permission).order_by(Permission.code).all()


register_crud_routes(
    router,
    Permission,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    require_permission("system.admin"),
    "permission"
)
