import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine
from routers import (
    announcements,
    auth,
    bulletins,
    calendar,
    contacts,
    coordinators,
    groups,
    members,
    programs,
    search,
    teams,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIU Church Bulletin API",
    description="REST API for the Asia-Pacific International University Church bulletin management system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers under /api/v1
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(bulletins.router, prefix=API_PREFIX)
app.include_router(programs.router, prefix=API_PREFIX)
app.include_router(coordinators.router, prefix=API_PREFIX)
app.include_router(announcements.router, prefix=API_PREFIX)
app.include_router(calendar.router, prefix=API_PREFIX)
app.include_router(members.router, prefix=API_PREFIX)
app.include_router(teams.router, prefix=API_PREFIX)
app.include_router(groups.router, prefix=API_PREFIX)
app.include_router(contacts.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)


@app.on_event("startup")
async def startup():
    """Log confirmation of DB connection on startup."""
    logger.info("AIU Church Bulletin API starting up...")
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection confirmed.")
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Wrap Pydantic validation errors in the standard response envelope."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "message": str(exc.errors()),
            "code": 422,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Wrap all unhandled exceptions in the standard response envelope."""
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", str(exc))
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": detail,
            "code": status_code,
        },
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"success": True, "message": "AIU Church Bulletin API is running"}
