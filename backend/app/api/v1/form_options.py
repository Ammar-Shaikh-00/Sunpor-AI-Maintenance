from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.company import Company
from app.models.dropdown_category import DropdownCategory
from app.models.dropdown_values import DropdownValue
from app.models.material_type import MaterialType
from app.models.production_line import ProductionLine
from app.models.shift import Shift
from app.permissions.check_permission import require_any_permission

router = APIRouter(prefix="/form-options")

form_dependency = require_any_permission(
    "production.view",
    "production.create",
    "event.create",
    "quality.create",
    "material_block.create",
    "system.admin",
)


@router.get("")
def get_form_options(
    db: Session = Depends(get_db),
    current_user=Depends(form_dependency),
):

    material_types = db.query(MaterialType).filter(
        MaterialType.is_deleted == False,
        MaterialType.active == True,
    ).all()

    shifts = db.query(Shift).order_by(Shift.name).all()

    companies = db.query(Company).filter(
        Company.is_deleted == False
    ).all()

    production_lines = db.query(ProductionLine).filter(
        ProductionLine.is_deleted == False,
        ProductionLine.active == True,
    ).all()

    categories = db.query(DropdownCategory).filter(
        DropdownCategory.is_deleted == False
    ).all()

    category_map = {category.id: category.code for category in categories}

    dropdown_values = db.query(DropdownValue).filter(
        DropdownValue.is_deleted == False,
        DropdownValue.active == True,
    ).order_by(DropdownValue.display_order).all()

    dropdowns: dict[str, list[dict]] = {}
    for value in dropdown_values:
        code = category_map.get(value.category_id)
        if not code:
            continue
        dropdowns.setdefault(code, []).append(
            {
                "id": str(value.id),
                "value": value.value,
                "display_order": value.display_order,
            }
        )

    return {
        "material_types": [
            {"id": item.id, "code": item.code, "description": item.description}
            for item in material_types
        ],
        "shifts": [
            {"id": item.id, "name": item.name}
            for item in shifts
        ],
        "companies": [
            {"id": item.id, "name": item.name}
            for item in companies
        ],
        "production_lines": [
            {
                "id": item.id,
                "name": item.name,
                "company_id": item.company_id,
            }
            for item in production_lines
        ],
        "dropdowns": dropdowns,
        "current_user_id": current_user.id,
    }


@router.get("/dropdowns/{category_code}")
def get_dropdown_values_by_code(
    category_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(form_dependency),
):

    category = db.query(DropdownCategory).filter(
        DropdownCategory.code == category_code,
        DropdownCategory.is_deleted == False,
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Dropdown category not found")

    values = db.query(DropdownValue).filter(
        DropdownValue.category_id == category.id,
        DropdownValue.is_deleted == False,
        DropdownValue.active == True,
    ).order_by(DropdownValue.display_order).all()

    return [
        {
            "id": str(value.id),
            "value": value.value,
            "display_order": value.display_order,
        }
        for value in values
    ]
