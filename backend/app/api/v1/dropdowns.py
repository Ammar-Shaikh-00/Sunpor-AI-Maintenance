from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.crud_utils import apply_updates
from app.api.v1.crud_utils import delete_object
from app.db.database import get_db
from app.models.dropdown_category import DropdownCategory
from app.models.dropdown_values import DropdownValue
from app.permissions.check_permission import require_permission
from app.schemas.data_models import DropdownCategoryCreate
from app.schemas.data_models import DropdownCategoryResponse
from app.schemas.data_models import DropdownCategoryUpdate
from app.schemas.data_models import DropdownValueCreate
from app.schemas.data_models import DropdownValueResponse
from app.schemas.data_models import DropdownValueUpdate


router = APIRouter()

dropdown_dependency = require_permission("system.admin")
categories_router = APIRouter(prefix="/dropdown-categories")
values_router = APIRouter(prefix="/dropdown-values")


def get_uuid_object_or_404(
    db: Session,
    model,
    object_id: UUID
):

    query = db.query(model).filter(
        model.id == object_id
    )

    if hasattr(model, "is_deleted"):
        query = query.filter(
            model.is_deleted == False
        )

    item = query.first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"{model.__name__} not found"
        )

    return item


@categories_router.get(
    "",
    response_model=list[DropdownCategoryResponse]
)
def list_dropdown_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    return db.query(DropdownCategory).filter(
        DropdownCategory.is_deleted == False
    ).offset(skip).limit(limit).all()


@categories_router.get(
    "/{category_id}",
    response_model=DropdownCategoryResponse
)
def get_dropdown_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    return get_uuid_object_or_404(
        db,
        DropdownCategory,
        category_id
    )


@categories_router.post(
    "",
    response_model=DropdownCategoryResponse,
    status_code=201
)
def create_dropdown_category(
    request: DropdownCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    item = DropdownCategory(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@categories_router.put(
    "/{category_id}",
    response_model=DropdownCategoryResponse
)
def update_dropdown_category(
    category_id: UUID,
    request: DropdownCategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    item = get_uuid_object_or_404(
        db,
        DropdownCategory,
        category_id
    )
    apply_updates(
        item,
        request
    )
    db.commit()
    db.refresh(item)

    return item


@categories_router.delete("/{category_id}")
def delete_dropdown_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    item = get_uuid_object_or_404(
        db,
        DropdownCategory,
        category_id
    )
    delete_object(
        db,
        item
    )
    db.commit()

    return {
        "message": "Dropdown category deleted"
    }


@values_router.get(
    "",
    response_model=list[DropdownValueResponse]
)
def list_dropdown_values(
    category_id: UUID | None = None,
    active: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    query = db.query(DropdownValue).filter(
        DropdownValue.is_deleted == False
    )

    if category_id is not None:
        query = query.filter(
            DropdownValue.category_id == category_id
        )

    if active is not None:
        query = query.filter(
            DropdownValue.active == active
        )

    return query.order_by(
        DropdownValue.display_order
    ).offset(skip).limit(limit).all()


@values_router.get(
    "/{value_id}",
    response_model=DropdownValueResponse
)
def get_dropdown_value(
    value_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    return get_uuid_object_or_404(
        db,
        DropdownValue,
        value_id
    )


@values_router.post(
    "",
    response_model=DropdownValueResponse,
    status_code=201
)
def create_dropdown_value(
    request: DropdownValueCreate,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    get_uuid_object_or_404(
        db,
        DropdownCategory,
        request.category_id
    )

    item = DropdownValue(**request.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@values_router.put(
    "/{value_id}",
    response_model=DropdownValueResponse
)
def update_dropdown_value(
    value_id: UUID,
    request: DropdownValueUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    item = get_uuid_object_or_404(
        db,
        DropdownValue,
        value_id
    )
    apply_updates(
        item,
        request
    )
    db.commit()
    db.refresh(item)

    return item


@values_router.delete("/{value_id}")
def delete_dropdown_value(
    value_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(dropdown_dependency)
):

    item = get_uuid_object_or_404(
        db,
        DropdownValue,
        value_id
    )
    delete_object(
        db,
        item
    )
    db.commit()

    return {
        "message": "Dropdown value deleted"
    }


router.include_router(categories_router)
router.include_router(values_router)
