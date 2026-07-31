from sqlalchemy.orm import Session

from app.models.dropdown_category import DropdownCategory
from app.models.dropdown_values import DropdownValue
from app.seeders.utils import get_or_create


DROPDOWN_DATA = {
    "event_level_1": [
        "Extruder",
        "Granulator",
        "Cleaning",
        "Malfunctions",
    ],
    "extruder_level_2": [
        "Heating Up",
        "Shutting Down",
        "Screen Change",
        "Nozzle",
        "Low Production",
    ],
    "extruder_heating_level_3": [
        "Starting Up",
    ],
    "extruder_shutdown_level_3": [
        "Clean Shutdown",
        "Running Empty",
        "Cooling Down",
    ],
    "extruder_screen_change_level_3": [
        "Reason",
    ],
    "extruder_nozzle_level_3": [
        "Nozzle Change",
        "Nozzle Flushing",
        "Nozzle Grinding",
    ],
    "extruder_low_production_level_3": [
        "Reason",
    ],
    "granulator_level_2": [
        "Knife",
    ],
    "granulator_knife_level_3": [
        "Knife Change",
        "Knife Grinding",
    ],
    "cleaning_level_2": [
        "Water Bath",
        "Centrifuge",
        "Cleaning Work",
    ],
    "cleaning_level_3": [
        "Reason",
    ],
    "fault_level_2": [
        "Mechanical Malfunction",
        "Electrical Malfunction",
    ],
    "fault_mechanical_level_3": [
        "Clearing Blockage",
        "Nozzle Clogged",
        "Knife Holder Clogged",
        "Centrifuge Clogged",
        "Material Plate Removed",
        "Reason",
    ],
    "fault_electrical_level_3": [
        "Power Outage",
        "Reason",
    ],
    "material_behavior_type": [
        "Lump Formation",
        "Twin Beads",
        "Material Outside Sieve Tolerance",
        "Too Little Pentane",
        "Too Much Pentane",
        "Poor Foaming Behavior",
    ],
    "material_block_reason": [
        "Twin Beads",
        "Cell Structure",
        "Wrong Recipe",
        "Grain Distribution / Sieve Analysis",
        "Other",
    ],
    "foaming_behavior": [
        "OK",
        "Not OK",
        "Bad",
    ],
    "trial_option": [
        "Yes",
        "No",
    ],
}


def seed_dropdowns(db: Session) -> dict[str, int]:

    categories_created = 0
    values_created = 0
    values_reactivated = 0
    values_deactivated = 0

    for code, values in DROPDOWN_DATA.items():
        label = code.replace("_", " ").title()
        category, category_created = get_or_create(
            db,
            DropdownCategory,
            lookup={"code": code},
            defaults={"name": label},
        )
        if category_created:
            categories_created += 1

        desired_values = set(values)

        for index, value in enumerate(values, start=1):
            existing = db.query(DropdownValue).filter(
                DropdownValue.category_id == category.id,
                DropdownValue.value == value,
            ).first()

            if existing:
                if existing.is_deleted or not existing.active:
                    existing.is_deleted = False
                    existing.active = True
                    values_reactivated += 1
                existing.display_order = index
                continue

            db.add(
                DropdownValue(
                    category_id=category.id,
                    value=value,
                    display_order=index,
                    active=True,
                )
            )
            values_created += 1

        stale_values = db.query(DropdownValue).filter(
            DropdownValue.category_id == category.id,
            DropdownValue.is_deleted == False,
        ).all()

        for item in stale_values:
            if item.value not in desired_values:
                item.active = False
                values_deactivated += 1

    db.commit()

    return {
        "dropdown_categories_created": categories_created,
        "dropdown_values_created": values_created,
        "dropdown_values_reactivated": values_reactivated,
        "dropdown_values_deactivated": values_deactivated,
    }
