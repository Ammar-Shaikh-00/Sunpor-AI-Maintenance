from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.production_line import ProductionLine
from app.seeders.utils import get_or_create


def seed_production_lines(db: Session) -> dict[str, int]:

    company, _ = get_or_create(
        db,
        Company,
        lookup={"name": "Sunpor"},
        defaults={
            "location": "SUNPOR",
            "description": "SUNPOR production company",
        },
    )

    _, created = get_or_create(
        db,
        ProductionLine,
        lookup={
            "company_id": company.id,
            "name": "Extrusion E10",
        },
        defaults={
            "description": "SUNPOR extrusion line E10",
            "active": True,
        },
    )

    db.commit()

    return {"production_lines_created": int(created)}
