import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.public import router as public_router
from app.api.v1.auth import router as auth_router
from app.api.v1.form_options import router as form_options_router
from app.api.v1.dropdowns import router as dropdowns_router
from app.api.v1.master_data import router as master_data_router
from app.api.v1.ml import router as ml_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.profile import router as profile_router
from app.api.v1.production_data import router as production_data_router
from app.api.v1.roles import router as roles_router
from app.api.v1.signals import router as signals_router
from app.api.v1.system_data import router as system_data_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware

os.environ.setdefault("LOG_DIR", settings.LOG_DIR)
os.environ.setdefault("LOG_LEVEL", settings.LOG_LEVEL)
os.environ.setdefault("LOG_MAX_BYTES", str(settings.LOG_MAX_BYTES))
os.environ.setdefault("LOG_BACKUP_COUNT", str(settings.LOG_BACKUP_COUNT))
os.environ.setdefault("SQLALCHEMY_LOG_LEVEL", settings.SQLALCHEMY_LOG_LEVEL)

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="SUNPOR Backend"
)

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(
    public_router,
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    roles_router,
    prefix="/roles",
    tags=["Roles"]
)

app.include_router(
    permissions_router,
    prefix="/permissions",
    tags=["Permissions"]
)

app.include_router(
    master_data_router,
    tags=["Master Data"]
)

app.include_router(
    production_data_router,
    tags=["Production Data"]
)

app.include_router(
    signals_router,
    tags=["Signals"]
)

app.include_router(
    form_options_router,
    tags=["Form Options"]
)

app.include_router(
    dropdowns_router,
    tags=["Dropdowns"]
)

app.include_router(
    ml_router,
    tags=["ML"]
)

app.include_router(
    system_data_router,
    tags=["System Data"]
)

app.include_router(
    profile_router,
    prefix="/profile",
    tags=["Profile"]
)


@app.on_event("startup")
def on_startup():
    logger.info(
        "SUNPOR Backend started | env=%s | app=%s",
        settings.APP_ENV,
        settings.APP_NAME,
    )


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "message": "SUNPOR Backend Running"
    }


def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SUNPOR Backend",
        version="1.0.0",
        description="SUNPOR Backend API",
        routes=app.routes
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault(
                "security",
                [{"BearerAuth": []}]
            )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
