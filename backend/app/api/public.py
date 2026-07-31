from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import (
    DISPLAY_TIMEZONE_REGIONS,
    get_display_timezone_label,
    get_display_timezone_region,
)
from app.db.database import get_db
from app.models.company import Company

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/app-info")
def get_app_info(db: Session = Depends(get_db)):
    company = db.query(Company).order_by(Company.id).first()
    company_name = company.name if company else None

    display_title = (
        f"{company_name} Predictive Maintenance"
        if company_name
        else settings.APP_NAME
    )

    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "company_name": company_name,
        "display_title": display_title,
        "tagline": settings.APP_TAGLINE,
        "display_timezone_region": get_display_timezone_region(),
        "display_timezone": get_display_timezone_label(),
        "display_timezone_options": list(DISPLAY_TIMEZONE_REGIONS.keys()),
    }
