from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Callable, Any

from app.core.datetime_utils import (
    normalize_datetimes_in_mapping,
    normalize_datetime_fields_on_instance,
)
from app.db.database import get_db


def get_object_or_404(
    db: Session,
    model,
    object_id
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


def apply_updates(
    item,
    request
):

    for field, value in request.model_dump(
        exclude_unset=True
    ).items():
        setattr(item, field, value)

    normalize_datetime_fields_on_instance(item)


def delete_object(
    db: Session,
    item
):

    if hasattr(item, "is_deleted"):
        item.is_deleted = True
    else:
        db.delete(item)


def register_crud_routes(
    router,
    model,
    create_schema,
    update_schema,
    response_schema,
    dependency,
    object_name: str,
    before_create: Callable[[Session, Any, Any], None] | None = None,
    before_update: Callable[[Session, Any, Any, Any], None] | None = None,
    before_delete: Callable[[Session, Any, Any], None] | None = None,
    delete_dependency=None
):

    delete_dependency = delete_dependency or dependency

    @router.get("", response_model=list[response_schema])
    def list_items(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user=Depends(dependency)
    ):

        query = db.query(model)

        if hasattr(model, "is_deleted"):
            query = query.filter(
                model.is_deleted == False
            )

        if hasattr(model, "created_at"):
            query = query.order_by(model.created_at.desc())
        elif hasattr(model, "event_time"):
            query = query.order_by(model.event_time.desc())
        elif hasattr(model, "input_time"):
            query = query.order_by(model.input_time.desc())
        elif hasattr(model, "start_time"):
            query = query.order_by(model.start_time.desc())
        elif hasattr(model, "from_time"):
            query = query.order_by(model.from_time.desc())

        return query.offset(skip).limit(limit).all()

    @router.get("/{object_id}", response_model=response_schema)
    def get_item(
        object_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(dependency)
    ):

        return get_object_or_404(
            db,
            model,
            object_id
        )

    @router.post("", response_model=response_schema, status_code=201)
    def create_item(
        request: create_schema,
        db: Session = Depends(get_db),
        current_user=Depends(dependency)
    ):
        if before_create:
            before_create(db, request, current_user)

        payload = normalize_datetimes_in_mapping(
            request.model_dump(exclude_none=True),
            model,
        )
        item = model(**payload)
        normalize_datetime_fields_on_instance(item)
        db.add(item)
        db.commit()
        db.refresh(item)

        return item

    @router.put("/{object_id}", response_model=response_schema)
    def update_item(
        object_id: int,
        request: update_schema,
        db: Session = Depends(get_db),
        current_user=Depends(dependency)
    ):

        item = get_object_or_404(
            db,
            model,
            object_id
        )
        if before_update:
            before_update(db, item, request, current_user)
        apply_updates(
            item,
            request
        )
        db.commit()
        db.refresh(item)

        return item

    @router.delete("/{object_id}")
    def delete_item(
        object_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(delete_dependency)
    ):

        item = get_object_or_404(
            db,
            model,
            object_id
        )
        if before_delete:
            before_delete(db, item, current_user)
        delete_object(
            db,
            item
        )
        db.commit()

        return {
            "message": f"{object_name} deleted"
        }

    list_items.__name__ = f"list_{object_name}"
    get_item.__name__ = f"get_{object_name}"
    create_item.__name__ = f"create_{object_name}"
    update_item.__name__ = f"update_{object_name}"
    delete_item.__name__ = f"delete_{object_name}"
