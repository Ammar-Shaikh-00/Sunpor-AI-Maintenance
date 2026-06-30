#!/bin/bash
set -e

LOG_DIR="${LOG_DIR:-/app/logs}"
mkdir -p "$LOG_DIR"

echo "Waiting for database..."
python - <<'EOF'
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging(settings.LOG_LEVEL)
logger = __import__("logging").getLogger("app.entrypoint")

for _ in range(30):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect():
            logger.info("Database is ready.")
            sys.exit(0)
    except OperationalError:
        time.sleep(2)

logger.error("Database not available after 60 seconds.")
sys.exit(1)
EOF

echo "Running migrations..."
alembic upgrade head

echo "Running seeders..."
python -m app.seeders.run_seeders

echo "Starting application..."
exec python -c "
from app.core.config import settings
from app.core.logging_config import setup_logging
import uvicorn

setup_logging(settings.LOG_LEVEL)
uvicorn.run(
    'app.main:app',
    host='0.0.0.0',
    port=8000,
    log_config=None,
)
"
