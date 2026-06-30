from fastapi import APIRouter

from app.api.v1.crud_utils import register_crud_routes
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.permissions.check_permission import require_permission
from app.schemas.data_models import AuditLogCreate
from app.schemas.data_models import AuditLogResponse
from app.schemas.data_models import AuditLogUpdate
from app.schemas.data_models import RefreshTokenCreate
from app.schemas.data_models import RefreshTokenResponse
from app.schemas.data_models import RefreshTokenUpdate


router = APIRouter()

audit_logs_router = APIRouter(prefix="/audit-logs")
refresh_tokens_router = APIRouter(prefix="/refresh-tokens")
admin_dependency = require_permission("system.admin")

register_crud_routes(
    audit_logs_router,
    AuditLog,
    AuditLogCreate,
    AuditLogUpdate,
    AuditLogResponse,
    admin_dependency,
    "audit_log"
)

register_crud_routes(
    refresh_tokens_router,
    RefreshToken,
    RefreshTokenCreate,
    RefreshTokenUpdate,
    RefreshTokenResponse,
    admin_dependency,
    "refresh_token"
)

router.include_router(audit_logs_router)
router.include_router(refresh_tokens_router)
