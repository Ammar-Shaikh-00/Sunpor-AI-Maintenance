from fastapi import APIRouter

from app.api.v1.crud_utils import register_crud_routes
from app.models.ml_prediction import MLPrediction
from app.permissions.check_permission import require_permission
from app.schemas.data_models import MLPredictionCreate
from app.schemas.data_models import MLPredictionResponse
from app.schemas.data_models import MLPredictionUpdate


router = APIRouter()

ml_predictions_router = APIRouter(prefix="/ml-predictions")

register_crud_routes(
    ml_predictions_router,
    MLPrediction,
    MLPredictionCreate,
    MLPredictionUpdate,
    MLPredictionResponse,
    require_permission("ml.view"),
    "ml_prediction"
)

router.include_router(ml_predictions_router)
