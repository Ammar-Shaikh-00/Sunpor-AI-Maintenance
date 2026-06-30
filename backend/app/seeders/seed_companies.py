from sqlalchemy.orm import Session

from app.models.company import Company
from app.seeders.utils import get_or_create


def seed_companies(db: Session) -> dict[str, int]:

    _, created = get_or_create(
        db,
        Company,
        lookup={"name": "Sunpor"},
        defaults={
            "location": "SUNPOR",
            "description": "SUNPOR production company",
        },
    )

    db.commit()

    return {"companies_created": int(created)}
