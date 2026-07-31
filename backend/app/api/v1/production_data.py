from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.crud_utils import register_crud_routes
from app.models.daily_quality import DailyQualityInput
from app.models.material_behaviour_event import MaterialBehaviorEvent
from app.models.material_block import MaterialBlock
from app.models.production_event import ProductionEvent
from app.models.production_run import ProductionRun
from app.models.enums import ProductionRunStatus
from app.permissions.check_permission import require_permission
from app.permissions.check_permission import require_super_admin
from app.schemas.data_models import DailyQualityInputCreate
from app.schemas.data_models import DailyQualityInputResponse
from app.schemas.data_models import DailyQualityInputUpdate
from app.schemas.data_models import MaterialBehaviorEventCreate
from app.schemas.data_models import MaterialBehaviorEventResponse
from app.schemas.data_models import MaterialBehaviorEventUpdate
from app.schemas.data_models import MaterialBlockCreate
from app.schemas.data_models import MaterialBlockResponse
from app.schemas.data_models import MaterialBlockUpdate
from app.schemas.data_models import ProductionEventCreate
from app.schemas.data_models import ProductionEventResponse
from app.schemas.data_models import ProductionEventUpdate
from app.schemas.data_models import ProductionRunCreate
from app.schemas.data_models import ProductionRunResponse
from app.schemas.data_models import ProductionRunUpdate


router = APIRouter()

production_runs_router = APIRouter(prefix="/production-runs")
production_events_router = APIRouter(prefix="/production-events")
material_behavior_router = APIRouter(prefix="/material-behavior-events")
material_blocks_router = APIRouter(prefix="/material-blocks")
daily_quality_router = APIRouter(prefix="/daily-quality-inputs")


def _ensure_single_running_run_per_line(
    db: Session,
    production_line_id: int,
    exclude_run_id: int | None = None,
) -> None:
    query = db.query(ProductionRun).filter(
        ProductionRun.production_line_id == production_line_id,
        ProductionRun.status == ProductionRunStatus.RUNNING,
    )

    if hasattr(ProductionRun, "is_deleted"):
        query = query.filter(ProductionRun.is_deleted == False)

    if exclude_run_id is not None:
        query = query.filter(ProductionRun.id != exclude_run_id)

    running_conflict = query.first()
    if running_conflict:
        raise HTTPException(
            status_code=400,
            detail=(
                "Another RUNNING production run already exists "
                f"for production_line_id={production_line_id}"
            ),
        )


def validate_production_run_create(db: Session, request, current_user) -> None:
    if request.status == ProductionRunStatus.RUNNING:
        _ensure_single_running_run_per_line(db, request.production_line_id)


def validate_production_run_update(db: Session, item, request, current_user) -> None:
    if item.status == ProductionRunStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Completed production runs cannot be edited",
        )

    updates = request.model_dump(exclude_unset=True)
    target_status = updates.get("status", item.status)
    target_line_id = updates.get("production_line_id", item.production_line_id)

    if target_status == ProductionRunStatus.RUNNING:
        _ensure_single_running_run_per_line(
            db,
            production_line_id=target_line_id,
            exclude_run_id=item.id,
        )


def _get_production_run(db: Session, production_run_id: int) -> ProductionRun:
    query = db.query(ProductionRun).filter(ProductionRun.id == production_run_id)
    if hasattr(ProductionRun, "is_deleted"):
        query = query.filter(ProductionRun.is_deleted == False)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")
    return run


def _ensure_production_run_is_editable(db: Session, production_run_id: int) -> None:
    run = _get_production_run(db, production_run_id)
    if run.status == ProductionRunStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify entries for a completed production run",
        )


def validate_linked_run_create(db: Session, request, current_user) -> None:
    _ensure_production_run_is_editable(db, request.production_run_id)


def validate_linked_run_update(db: Session, item, request, current_user) -> None:
    updates = request.model_dump(exclude_unset=True)
    run_id = updates.get("production_run_id", item.production_run_id)
    _ensure_production_run_is_editable(db, run_id)


def validate_linked_run_delete(db: Session, item, current_user) -> None:
    _ensure_production_run_is_editable(db, item.production_run_id)


def validate_production_run_delete(db: Session, item, current_user) -> None:
    if item.status == ProductionRunStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Completed production runs cannot be deleted",
        )

register_crud_routes(
    production_runs_router,
    ProductionRun,
    ProductionRunCreate,
    ProductionRunUpdate,
    ProductionRunResponse,
    require_permission("production.view"),
    "production_run",
    before_create=validate_production_run_create,
    before_update=validate_production_run_update,
    before_delete=validate_production_run_delete,
    delete_dependency=require_super_admin(),
)

register_crud_routes(
    production_events_router,
    ProductionEvent,
    ProductionEventCreate,
    ProductionEventUpdate,
    ProductionEventResponse,
    require_permission("event.view"),
    "production_event",
    before_create=validate_linked_run_create,
    before_update=validate_linked_run_update,
    before_delete=validate_linked_run_delete,
    delete_dependency=require_super_admin(),
)

register_crud_routes(
    material_behavior_router,
    MaterialBehaviorEvent,
    MaterialBehaviorEventCreate,
    MaterialBehaviorEventUpdate,
    MaterialBehaviorEventResponse,
    require_permission("quality.view"),
    "material_behavior_event",
    before_create=validate_linked_run_create,
    before_update=validate_linked_run_update,
    before_delete=validate_linked_run_delete,
    delete_dependency=require_super_admin(),
)

register_crud_routes(
    material_blocks_router,
    MaterialBlock,
    MaterialBlockCreate,
    MaterialBlockUpdate,
    MaterialBlockResponse,
    require_permission("material_block.view"),
    "material_block",
    before_create=validate_linked_run_create,
    before_update=validate_linked_run_update,
    before_delete=validate_linked_run_delete,
    delete_dependency=require_super_admin(),
)

register_crud_routes(
    daily_quality_router,
    DailyQualityInput,
    DailyQualityInputCreate,
    DailyQualityInputUpdate,
    DailyQualityInputResponse,
    require_permission("quality.view"),
    "daily_quality_input",
    before_create=validate_linked_run_create,
    before_update=validate_linked_run_update,
    before_delete=validate_linked_run_delete,
    delete_dependency=require_super_admin(),
)

router.include_router(production_runs_router)
router.include_router(production_events_router)
router.include_router(material_behavior_router)
router.include_router(material_blocks_router)
router.include_router(daily_quality_router)
