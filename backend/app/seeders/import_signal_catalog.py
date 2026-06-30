import argparse
import csv
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.machine_area import MachineArea
from app.models.production_line import ProductionLine
from app.models.signal_catalog import SignalCatalog


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
}

REQUIRED_COLUMNS = {
    "Tag WinCC (OPC)": "wincc_tag",
    "Faktor": "factor",
    "Einheit": "unit",
    "Datentyp": "datatype",
    "Bezeichnung": "display_name",
}

CSV_REQUIRED_COLUMNS = {
    "wincc_tag",
    "display_name",
    "unit",
    "datatype",
    "factor",
    "signal_group",
    "signal_role",
    "machine_area",
    "active",
}


def normalize(value: str):

    value = unicodedata.normalize(
        "NFKD",
        value or ""
    )
    value = value.encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    return value.lower()


def column_index(cell_ref: str):

    letters = "".join(
        char
        for char in cell_ref
        if char.isalpha()
    )

    index = 0

    for letter in letters:
        index = index * 26 + ord(letter.upper()) - ord("A") + 1

    return index - 1


def read_shared_strings(workbook: zipfile.ZipFile):

    path = "xl/sharedStrings.xml"

    if path not in workbook.namelist():
        return []

    root = ElementTree.fromstring(
        workbook.read(path)
    )

    strings = []

    for item in root.findall("a:si", NS):
        strings.append(
            "".join(
                text.text or ""
                for text in item.findall(".//a:t", NS)
            )
        )

    return strings


def read_xlsx_rows(file_path: Path):

    with zipfile.ZipFile(file_path) as workbook:
        shared_strings = read_shared_strings(workbook)
        sheet = ElementTree.fromstring(
            workbook.read("xl/worksheets/sheet1.xml")
        )

        rows = []

        for row in sheet.findall(".//a:sheetData/a:row", NS):
            values = []

            for cell in row.findall("a:c", NS):
                index = column_index(
                    cell.get("r", "A1")
                )

                while len(values) <= index:
                    values.append("")

                value = cell.find("a:v", NS)
                value = "" if value is None else value.text

                if cell.get("t") == "s" and value != "":
                    value = shared_strings[int(value)]

                values[index] = value

            rows.append(values)

    return rows


def to_float(value: str):

    if value is None or value == "":
        return 1.0

    return float(
        str(value).replace(",", ".")
    )


def to_bool(value: str):

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "active",
    }


def infer_machine_area(
    wincc_tag: str,
    display_name: str
):

    text = normalize(
        f"{wincc_tag} {display_name}"
    )

    if "antistatik" in text:
        return "Antistatic"

    if "offspec" in text or "ausschuss" in text or "sieb grob" in text or "sieb fein" in text:
        return "Off-spec / Scrap"

    if "material produktion" in text:
        return "Material Production"

    if "pentan" in text or "stickstoff" in text:
        return "Pentane / Nitrogen"

    if "dosierer" in text or "waage" in text:
        return "Feeder"

    if "granulator" in text or "messer" in text or "hydraulik" in text:
        return "Granulator"

    if "wasser" in text or "prozesswasser" in text or "wasserpumpe" in text:
        return "Water Box / Process Water"

    if "anfahrventil" in text:
        return "Startup Valve"

    if "siebwechsler" in text or "lochplatte" in text:
        return "Screen Changer"

    if "schmelzepumpe" in text:
        return "Melt Pump"

    if "massedruck" in text or "massetemperatur" in text:
        return "Melt Pressure"

    if (
        "heizzone" in text
        or "zylinder zone" in text
        or "flansch" in text
        or "materialaustragsteil" in text
    ):
        return "Extruder Heating Zones"

    return "General"


def infer_signal_group(
    wincc_tag: str,
    display_name: str
):

    text = normalize(
        f"{wincc_tag} {display_name}"
    )

    checks = [
        ("temperatur", "temperature"),
        ("druck", "pressure"),
        ("durchfluss", "flow"),
        ("flow", "flow"),
        ("drehzahl", "speed"),
        ("torque", "torque"),
        ("drehmoment", "torque"),
        ("durchsatz", "throughput"),
        ("frequenz", "frequency"),
        ("menge", "quantity"),
        ("masse", "quantity"),
        ("position", "position"),
        ("anpresskraft", "force"),
        ("fehler", "error"),
        ("betriebsart", "mode"),
        ("material", "material"),
    ]

    for needle, group in checks:
        if needle in text:
            return group

    return "general"


def infer_signal_role(
    wincc_tag: str,
    display_name: str
):

    text = normalize(
        f"{wincc_tag} {display_name}"
    )

    if "sollwert" in text or "soll" in text or "setpoint" in text:
        return "setpoint"

    if "istwert" in text or " ist" in text or "actual" in text:
        return "actual"

    if "stell" in text:
        return "control_output"

    if "fehler" in text:
        return "error_code"

    if "betriebsart" in text:
        return "operating_mode"

    return "measurement"


def map_rows(rows: list[list[str]]):

    if not rows:
        return []

    header = rows[0]
    indexes = {}

    for column_name, field_name in REQUIRED_COLUMNS.items():
        if column_name not in header:
            raise ValueError(
                f"Missing required column: {column_name}"
            )

        indexes[field_name] = header.index(column_name)

    records = []

    for row in rows[1:]:
        wincc_tag = row[indexes["wincc_tag"]].strip()

        if not wincc_tag:
            continue

        display_name = row[indexes["display_name"]].strip()

        records.append(
            {
                "wincc_tag": wincc_tag,
                "display_name": display_name or wincc_tag,
                "unit": row[indexes["unit"]].strip(),
                "datatype": row[indexes["datatype"]].strip(),
                "factor": to_float(row[indexes["factor"]]),
                "machine_area": infer_machine_area(
                    wincc_tag,
                    display_name
                ),
                "signal_group": infer_signal_group(
                    wincc_tag,
                    display_name
                ),
                "signal_role": infer_signal_role(
                    wincc_tag,
                    display_name
                ),
            }
        )

    return records


def read_csv_records(file_path: Path):

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if not reader.fieldnames:
            return []

        missing_columns = CSV_REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(sorted(missing_columns))
            )

        records = []

        for row in reader:
            wincc_tag = row["wincc_tag"].strip()

            if not wincc_tag:
                continue

            display_name = row["display_name"].strip()

            records.append(
                {
                    "wincc_tag": wincc_tag,
                    "display_name": display_name or wincc_tag,
                    "unit": row["unit"].strip(),
                    "datatype": row["datatype"].strip(),
                    "factor": to_float(row["factor"]),
                    "signal_group": row["signal_group"].strip(),
                    "signal_role": row["signal_role"].strip(),
                    "machine_area": row["machine_area"].strip(),
                    "active": to_bool(row["active"]),
                }
            )

    return records


def read_signal_records(file_path: Path):

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return read_csv_records(file_path)

    if suffix == ".xlsx":
        return map_rows(
            read_xlsx_rows(file_path)
        )

    raise ValueError(
        "Unsupported signal catalog file type. Use .csv or .xlsx"
    )


def get_or_create_company(
    db: Session,
    company_name: str
):

    company = db.query(Company).filter(
        Company.name == company_name
    ).first()

    if company:
        return company

    company = Company(
        name=company_name,
        location="SUNPOR",
        description="SUNPOR production company"
    )
    db.add(company)
    db.flush()

    return company


def get_or_create_production_line(
    db: Session,
    company: Company,
    line_name: str
):

    line = db.query(ProductionLine).filter(
        ProductionLine.company_id == company.id,
        ProductionLine.name == line_name
    ).first()

    if line:
        return line

    line = ProductionLine(
        company_id=company.id,
        name=line_name,
        description="SUNPOR extrusion line",
        active=True
    )
    db.add(line)
    db.flush()

    return line


def get_or_create_machine_area(
    db: Session,
    production_line: ProductionLine,
    area_name: str
):

    area = db.query(MachineArea).filter(
        MachineArea.production_line_id == production_line.id,
        MachineArea.name == area_name
    ).first()

    if area:
        return area

    area = MachineArea(
        production_line_id=production_line.id,
        name=area_name,
        type=area_name
    )
    db.add(area)
    db.flush()

    return area


def import_signal_catalog(
    db: Session,
    file_path: Path,
    company_name: str,
    line_name: str
):

    records = read_signal_records(file_path)

    company = get_or_create_company(
        db,
        company_name
    )
    production_line = get_or_create_production_line(
        db,
        company,
        line_name
    )

    machine_areas = {}
    created = 0
    updated = 0

    for record in records:
        area_name = record.pop("machine_area")

        if area_name not in machine_areas:
            machine_areas[area_name] = get_or_create_machine_area(
                db,
                production_line,
                area_name
            )

        signal = db.query(SignalCatalog).filter(
            SignalCatalog.wincc_tag == record["wincc_tag"]
        ).first()

        values = {
            **record,
            "company_id": company.id,
            "production_line_id": production_line.id,
            "machine_area_id": machine_areas[area_name].id,
            "description": f"Imported from {file_path.name}",
        }

        if signal:
            for field, value in values.items():
                setattr(
                    signal,
                    field,
                    value
                )
            updated += 1
        else:
            db.add(
                SignalCatalog(**values)
            )
            created += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "total": len(records),
        "machine_areas": sorted(machine_areas.keys()),
    }


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SIGNAL_CATALOG_FILE = BACKEND_ROOT / "seed_data" / "signal_catalog_seed.csv"
FALLBACK_SIGNAL_CATALOG_FILE = PROJECT_ROOT / "Docs" / "signal_catalog_seed.csv"


def resolve_signal_catalog_file(file_path: Path | None = None) -> Path:

    if file_path is not None:
        return file_path

    if DEFAULT_SIGNAL_CATALOG_FILE.exists():
        return DEFAULT_SIGNAL_CATALOG_FILE

    if FALLBACK_SIGNAL_CATALOG_FILE.exists():
        return FALLBACK_SIGNAL_CATALOG_FILE

    return DEFAULT_SIGNAL_CATALOG_FILE


def seed_signal_catalog(
    db: Session,
    file_path: Path | None = None,
    company_name: str = "Sunpor",
    line_name: str = "Extrusion E10",
):

    catalog_file = resolve_signal_catalog_file(file_path)

    if not catalog_file.exists():
        raise FileNotFoundError(
            f"Signal catalog file not found: {catalog_file}"
        )

    return import_signal_catalog(
        db,
        catalog_file,
        company_name,
        line_name,
    )


def run():

    parser = argparse.ArgumentParser(
        description="Import signal catalog CSV/XLSX into signal_catalog"
    )
    parser.add_argument(
        "file_path",
        help="Path to SignalExport.xlsx"
    )
    parser.add_argument(
        "--company",
        default="Sunpor"
    )
    parser.add_argument(
        "--line",
        default="Extrusion E10"
    )

    args = parser.parse_args()
    file_path = Path(args.file_path)

    db = SessionLocal()

    try:
        result = seed_signal_catalog(
            db,
            file_path=file_path,
            company_name=args.company,
            line_name=args.line,
        )
        print(
            "Signal catalog import completed."
        )
        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    run()
