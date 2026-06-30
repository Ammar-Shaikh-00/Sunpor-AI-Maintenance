from sqlalchemy.orm import Session

from app.models.material_type import MaterialType
from app.seeders.utils import get_or_create


MATERIAL_TYPES = [
    "750",
    "750GEN2",
    "750PremGEN2",
    "753",
    "753PremGEN2",
]


def seed_material_types(db: Session) -> dict[str, int]:

    created = 0

    for code in MATERIAL_TYPES:
        _, was_created = get_or_create(
            db,
            MaterialType,
            lookup={"code": code},
            defaults={"active": True},
        )
        if was_created:
            created += 1

    db.commit()

    return {"material_types_created": created}
