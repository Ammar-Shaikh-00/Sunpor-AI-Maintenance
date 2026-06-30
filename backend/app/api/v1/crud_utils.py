from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

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
    object_name: str
):

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

        item = model(
            **request.model_dump(
                exclude_none=True
            )
        )
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
        current_user=Depends(dependency)
    ):

        item = get_object_or_404(
            db,
            model,
            object_id
        )
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
