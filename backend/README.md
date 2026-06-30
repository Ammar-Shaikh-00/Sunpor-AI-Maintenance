# SUNPOR Backend

FastAPI backend for the SUNPOR predictive AI system.

## Tech Stack

- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL / TimescaleDB
- JWT authentication
- RBAC permissions

## Requirements

- Python 3.12
- PostgreSQL running locally
- Database matching `.env`:

```env
DATABASE_URL=postgresql+psycopg2://sunpor_user:sunpor_password@localhost:5432/sunpor_db
```

Create the PostgreSQL user/database if they do not already exist.

## First-Time Setup

From the backend directory:

```powershell
cd C:\Users\Hassam\Desktop\AI\Sanpor-Predictive-AI\backend
```

Create and activate a virtual environment if `my-env` does not already exist:

```powershell
python -m venv my-env
.\my-env\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Apply database migrations:

```powershell
alembic upgrade head
```

Seed initial data:

```powershell
python -m app.seeders.run_seeders
```

This creates roles, permissions, material types, shifts, and the SuperAdmin user.

Default admin:

```text
Email: admin@sunpor.local
Password: Admin@123456
```

## Start Backend

Activate the virtual environment:

```powershell
cd C:\Users\Hassam\Desktop\AI\Sanpor-Predictive-AI\backend
.\my-env\Scripts\Activate.ps1
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API root: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

For LAN access, other developers should use your machine IP, for example:

```text
http://192.168.1.50:8000/docs
```

## Daily Development Commands

Run migrations after pulling backend changes:

```powershell
alembic upgrade head
```

Run seeders again if seed data changed:

```powershell
python -m app.seeders.run_seeders
```

Import the boss signal catalog seed file into `signal_catalog`:

```powershell
python -m app.seeders.import_signal_catalog "C:\Users\Hassam\Desktop\AI\Sanpor-Predictive-AI\Docs\signal_catalog_seed.csv"
```

This command creates/updates:

- `companies`
- `production_lines`
- `machine_areas`
- `signal_catalog`

Signals are matched by `wincc_tag`, so running the import again updates existing rows instead of creating duplicates.

The importer also still supports the original `SignalExport.xlsx` file if needed.

Start server:

```powershell
uvicorn app.main:app --reload
```

## Authentication Flow

Login:

```http
POST /auth/login
```

Body:

```json
{
  "email": "admin@sunpor.local",
  "password": "Admin@123456"
}
```

Use the returned token in Swagger by clicking **Authorize** and entering:

```text
Bearer YOUR_ACCESS_TOKEN
```

## Important API Groups

- `/auth` - login, logout, current user, password APIs
- `/users` - user CRUD and role assignment
- `/roles` - role CRUD and permission assignment
- `/permissions` - permission CRUD
- `/companies`, `/production-lines`, `/machine-areas` - master data
- `/production-runs`, `/production-events` - production records
- `/material-behavior-events`, `/material-blocks`, `/daily-quality-inputs` - quality and material labels
- `/signal-catalog`, `/signal-timeseries` - signal metadata and historical values
- `/ml-predictions` - ML output storage
- `/dropdown-categories`, `/dropdown-values` - configurable dropdown data

## Database Migrations

Create a new migration after model changes:

```powershell
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```powershell
alembic upgrade head
```

Check current migration:

```powershell
alembic current
```

## Troubleshooting

If `uvicorn` is not recognized, make sure the virtual environment is activated and dependencies are installed:

```powershell
.\my-env\Scripts\Activate.ps1
pip install -r requirements.txt
```

If the backend cannot connect to the database, verify PostgreSQL is running and `.env` has the correct `DATABASE_URL`.

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
