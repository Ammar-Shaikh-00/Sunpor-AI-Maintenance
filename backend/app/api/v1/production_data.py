from fastapi import APIRouter

from app.api.v1.crud_utils import register_crud_routes
from app.models.daily_quality import DailyQualityInput
from app.models.material_behaviour_event import MaterialBehaviorEvent
from app.models.material_block import MaterialBlock
from app.models.production_event import ProductionEvent
from app.models.production_run import ProductionRun
from app.permissions.check_permission import require_permission
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

register_crud_routes(
    production_runs_router,
    ProductionRun,
    ProductionRunCreate,
    ProductionRunUpdate,
    ProductionRunResponse,
    require_permission("production.view"),
    "production_run"
)

register_crud_routes(
    production_events_router,
    ProductionEvent,
    ProductionEventCreate,
    ProductionEventUpdate,
    ProductionEventResponse,
    require_permission("event.view"),
    "production_event"
)

register_crud_routes(
    material_behavior_router,
    MaterialBehaviorEvent,
    MaterialBehaviorEventCreate,
    MaterialBehaviorEventUpdate,
    MaterialBehaviorEventResponse,
    require_permission("quality.view"),
    "material_behavior_event"
)

register_crud_routes(
    material_blocks_router,
    MaterialBlock,
    MaterialBlockCreate,
    MaterialBlockUpdate,
    MaterialBlockResponse,
    require_permission("material_block.view"),
    "material_block"
)

register_crud_routes(
    daily_quality_router,
    DailyQualityInput,
    DailyQualityInputCreate,
    DailyQualityInputUpdate,
    DailyQualityInputResponse,
    require_permission("quality.view"),
    "daily_quality_input"
)

router.include_router(production_runs_router)
router.include_router(production_events_router)
router.include_router(material_behavior_router)
router.include_router(material_blocks_router)
router.include_router(daily_quality_router)
