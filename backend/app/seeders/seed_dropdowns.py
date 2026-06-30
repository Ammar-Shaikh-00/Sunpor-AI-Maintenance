from sqlalchemy.orm import Session

from app.models.dropdown_category import DropdownCategory
from app.models.dropdown_values import DropdownValue
from app.seeders.utils import get_or_create


DROPDOWN_DATA = {
    "event_level_1": [
        "Extruder",
        "Granulator",
        "Cleaning",
        "Faults",
    ],
    "extruder_level_2": [
        "Heating Up",
        "Shutdown",
        "Screen Change",
        "Nozzle",
    ],
    "extruder_level_3": [
        "Startup",
        "Cleaning Run",
        "Empty Run",
        "Cooling Down",
        "Reason",
        "Nozzle Change",
        "Nozzle Flushing",
        "Nozzle Grinding",
    ],
    "granulator_level_2": ["Knife"],
    "granulator_level_3": [
        "Knife Change",
        "Knife Sharpening",
    ],
    "cleaning_level_2": [
        "Water Basin",
        "Centrifuge",
        "Cleaning Work",
    ],
    "cleaning_level_3": [
        "Water Basin",
        "Centrifuge",
        "Cleaning Work",
    ],
    "fault_level_2": [
        "Mechanical Fault",
        "Electrical Fault",
    ],
    "fault_mechanical_level_3": [
        "Chiseling Free",
        "Nozzle Blockage",
        "Knife Holder Blockage",
        "Centrifuge Clogged",
        "Material Plate Removed",
        "Other",
    ],
    "fault_electrical_level_3": [
        "Power Failure",
        "Other",
    ],
    "material_behavior_type": [
        "Lump Formation",
        "Twin Beads",
        "Material Outside Sieve Tolerance",
        "Material Too Little Pentane",
        "Material Too Much Pentane",
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
    ],
    "trial_option": [
        "Yes",
        "No",
    ],
}


def seed_dropdowns(db: Session) -> dict[str, int]:

    categories_created = 0
    values_created = 0

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

        for index, value in enumerate(values, start=1):
            existing = db.query(DropdownValue).filter(
                DropdownValue.category_id == category.id,
                DropdownValue.value == value,
                DropdownValue.is_deleted == False,
            ).first()

            if existing:
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

    db.commit()

    return {
        "dropdown_categories_created": categories_created,
        "dropdown_values_created": values_created,
    }
