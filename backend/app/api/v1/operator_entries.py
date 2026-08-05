from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import (
    normalize_datetime_fields_on_instance,
    normalize_datetimes_in_mapping,
)
from app.db.database import get_db
from app.models.operator_entry import OperatorEntry
from app.models.production_run import ProductionRun
from app.models.user import User
from app.permissions.check_permission import require_permission, require_super_admin
from app.schemas.operator_entry import (
    OPERATOR_CATEGORIES,
    OperatorEntryCreate,
    OperatorEntryListResponse,
    OperatorEntryResponse,
    OperatorEntryUpdate,
)

router = APIRouter(prefix="/operator-entries", tags=["Operator Entries"])

view_dependency = require_permission("event.view")
mutate_dependency = require_permission("event.view")
delete_dependency = require_super_admin()


def _serialize(entry: OperatorEntry) -> OperatorEntryResponse:
    return OperatorEntryResponse.model_validate(entry)


def _get_entry_or_404(db: Session, entry_id: int) -> OperatorEntry:
    entry = (
        db.query(OperatorEntry)
        .options(
            joinedload(OperatorEntry.operator),
            joinedload(OperatorEntry.production_run),
            joinedload(OperatorEntry.updated_by),
        )
        .filter(OperatorEntry.id == entry_id, OperatorEntry.is_deleted == False)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Operator entry not found")
    return entry


def _resolve_company_id(db: Session, payload: OperatorEntryCreate, user: User) -> int:
    if payload.production_run_id:
        run = (
            db.query(ProductionRun)
            .filter(
                ProductionRun.id == payload.production_run_id,
                ProductionRun.is_deleted == False,
            )
            .first()
        )
        if not run:
            raise HTTPException(status_code=404, detail="Production run not found")
        return run.company_id

    # Fallback: most recent run's company (operators are not company-scoped on User).
    latest_run = (
        db.query(ProductionRun)
        .filter(ProductionRun.is_deleted == False)
        .order_by(ProductionRun.id.desc())
        .first()
    )
    if latest_run:
        return latest_run.company_id

    raise HTTPException(
        status_code=400,
        detail="production_run_id is required to create an operator entry",
    )


@router.get("", response_model=OperatorEntryListResponse)
def list_operator_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    category: list[str] | None = Query(default=None),
    status: list[str] | None = Query(default=None),
    production_run_id: int | None = None,
    operator_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = Query("newest", pattern="^(newest|oldest|run|machine)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(view_dependency),
):
    query = db.query(OperatorEntry).filter(OperatorEntry.is_deleted == False)

    if category:
        invalid = [c for c in category if c not in OPERATOR_CATEGORIES]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid category: {invalid}")
        query = query.filter(OperatorEntry.category.in_(category))

    if status:
        query = query.filter(OperatorEntry.status.in_(status))

    if production_run_id is not None:
        query = query.filter(OperatorEntry.production_run_id == production_run_id)

    if operator_id is not None:
        query = query.filter(OperatorEntry.operator_id == operator_id)

    if date_from is not None:
        query = query.filter(OperatorEntry.event_time >= date_from)

    if date_to is not None:
        query = query.filter(OperatorEntry.event_time <= date_to)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                OperatorEntry.title.ilike(term),
                OperatorEntry.comment.ilike(term),
                OperatorEntry.batch_label.ilike(term),
                OperatorEntry.material_label.ilike(term),
                OperatorEntry.recipe_label.ilike(term),
                OperatorEntry.machine_label.ilike(term),
                OperatorEntry.category.ilike(term),
            )
        )

    total = query.count()

    if sort == "oldest":
        query = query.order_by(OperatorEntry.event_time.asc(), OperatorEntry.id.asc())
    elif sort == "run":
        query = query.order_by(
            OperatorEntry.production_run_id.asc(),
            OperatorEntry.event_time.desc(),
        )
    elif sort == "machine":
        query = query.order_by(
            OperatorEntry.machine_label.asc(),
            OperatorEntry.event_time.desc(),
        )
    else:
        query = query.order_by(OperatorEntry.event_time.desc(), OperatorEntry.id.desc())

    items = (
        query.options(
            joinedload(OperatorEntry.operator),
            joinedload(OperatorEntry.production_run),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return OperatorEntryListResponse(
        items=[_serialize(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{entry_id}", response_model=OperatorEntryResponse)
def get_operator_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(view_dependency),
):
    return _serialize(_get_entry_or_404(db, entry_id))


@router.post("", response_model=OperatorEntryResponse, status_code=201)
def create_operator_entry(
    request: OperatorEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(mutate_dependency),
):
    data = normalize_datetimes_in_mapping(request.model_dump(), OperatorEntry)
    company_id = _resolve_company_id(db, request, current_user)

    entry = OperatorEntry(
        company_id=company_id,
        operator_id=current_user.id,
        updated_by_id=current_user.id,
        **data,
    )
    normalize_datetime_fields_on_instance(entry)
    db.add(entry)
    db.commit()
    return _serialize(_get_entry_or_404(db, entry.id))


@router.put("/{entry_id}", response_model=OperatorEntryResponse)
def update_operator_entry(
    entry_id: int,
    request: OperatorEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(mutate_dependency),
):
    entry = _get_entry_or_404(db, entry_id)
    updates = normalize_datetimes_in_mapping(
        request.model_dump(exclude_unset=True),
        OperatorEntry,
    )
    for field, value in updates.items():
        setattr(entry, field, value)
    entry.updated_by_id = current_user.id
    normalize_datetime_fields_on_instance(entry)
    db.commit()
    return _serialize(_get_entry_or_404(db, entry.id))


@router.post("/{entry_id}/duplicate", response_model=OperatorEntryResponse, status_code=201)
def duplicate_operator_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(mutate_dependency),
):
    source = _get_entry_or_404(db, entry_id)
    clone = OperatorEntry(
        company_id=source.company_id,
        category=source.category,
        production_run_id=source.production_run_id,
        event_time=source.event_time,
        title=f"{source.title} (Kopie)",
        status=source.status,
        operator_id=current_user.id,
        updated_by_id=current_user.id,
        batch_label=source.batch_label,
        material_label=source.material_label,
        recipe_label=source.recipe_label,
        machine_label=source.machine_label,
        comment=source.comment,
        payload=dict(source.payload or {}),
    )
    normalize_datetime_fields_on_instance(clone)
    db.add(clone)
    db.commit()
    return _serialize(_get_entry_or_404(db, clone.id))


@router.delete("/{entry_id}", status_code=204)
def delete_operator_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(delete_dependency),
):
    entry = _get_entry_or_404(db, entry_id)
    entry.is_deleted = True
    entry.updated_by_id = current_user.id
    db.commit()
    return None
