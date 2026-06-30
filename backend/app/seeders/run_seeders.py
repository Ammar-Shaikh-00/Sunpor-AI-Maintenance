import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import SessionLocal
from app.seeders.assign_permissions import assign_permissions
from app.seeders.import_signal_catalog import seed_signal_catalog
from app.seeders.seed_dropdowns import seed_dropdowns
from app.seeders.seed_companies import seed_companies
from app.seeders.seed_material_types import seed_material_types
from app.seeders.seed_permissions import seed_permissions
from app.seeders.seed_production_lines import seed_production_lines
from app.seeders.seed_roles import seed_roles
from app.seeders.seed_role_permissions import seed_role_permissions
from app.seeders.seed_shifts import seed_shifts
from app.seeders.seed_super_admin import seed_super_admin


def run():

    """
    Idempotent seeders for Docker/production redeploys.

    Each step checks whether records already exist before inserting.
    Re-running seeders updates signal catalog entries by wincc_tag but
    does not create duplicate roles, users, companies, or permissions.
    """

    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("app.seeders")

    db = SessionLocal()

    try:
        logger.info("Starting idempotent database seeding")

        results = {}
        results.update(seed_roles(db))
        results.update(seed_permissions(db))
        results.update(seed_material_types(db))
        results.update(seed_shifts(db))
        results.update(seed_companies(db))
        results.update(seed_production_lines(db))
        results.update(assign_permissions(db))
        results.update(seed_role_permissions(db))
        results.update(seed_super_admin(db))
        results.update(seed_dropdowns(db))

        signal_result = seed_signal_catalog(db)
        results.update(
            {
                "signal_catalog_created": signal_result["created"],
                "signal_catalog_updated": signal_result["updated"],
                "signal_catalog_total": signal_result["total"],
            }
        )

        logger.info("Seeding completed | %s", results)

    finally:
        db.close()


if __name__ == "__main__":
    run()
