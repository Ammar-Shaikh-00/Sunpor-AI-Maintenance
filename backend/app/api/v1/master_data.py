from fastapi import APIRouter

from app.api.v1.crud_utils import register_crud_routes
from app.models.company import Company
from app.models.machine_area import MachineArea
from app.models.material_type import MaterialType
from app.models.production_line import ProductionLine
from app.models.shift import Shift
from app.permissions.check_permission import require_permission
from app.schemas.data_models import CompanyCreate
from app.schemas.data_models import CompanyResponse
from app.schemas.data_models import CompanyUpdate
from app.schemas.data_models import MachineAreaCreate
from app.schemas.data_models import MachineAreaResponse
from app.schemas.data_models import MachineAreaUpdate
from app.schemas.data_models import MaterialTypeCreate
from app.schemas.data_models import MaterialTypeResponse
from app.schemas.data_models import MaterialTypeUpdate
from app.schemas.data_models import ProductionLineCreate
from app.schemas.data_models import ProductionLineResponse
from app.schemas.data_models import ProductionLineUpdate
from app.schemas.data_models import ShiftCreate
from app.schemas.data_models import ShiftResponse
from app.schemas.data_models import ShiftUpdate


router = APIRouter()

admin_dependency = require_permission("system.admin")

companies_router = APIRouter(prefix="/companies")
production_lines_router = APIRouter(prefix="/production-lines")
machine_areas_router = APIRouter(prefix="/machine-areas")
material_types_router = APIRouter(prefix="/material-types")
shifts_router = APIRouter(prefix="/shifts")

register_crud_routes(
    companies_router,
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    admin_dependency,
    "company"
)

register_crud_routes(
    production_lines_router,
    ProductionLine,
    ProductionLineCreate,
    ProductionLineUpdate,
    ProductionLineResponse,
    admin_dependency,
    "production_line"
)

register_crud_routes(
    machine_areas_router,
    MachineArea,
    MachineAreaCreate,
    MachineAreaUpdate,
    MachineAreaResponse,
    admin_dependency,
    "machine_area"
)

register_crud_routes(
    material_types_router,
    MaterialType,
    MaterialTypeCreate,
    MaterialTypeUpdate,
    MaterialTypeResponse,
    admin_dependency,
    "material_type"
)

register_crud_routes(
    shifts_router,
    Shift,
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    admin_dependency,
    "shift"
)

router.include_router(companies_router)
router.include_router(production_lines_router)
router.include_router(machine_areas_router)
router.include_router(material_types_router)
router.include_router(shifts_router)
