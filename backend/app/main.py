"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=None)
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str] | JSONResponse:
    """Report API and database availability."""
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "version": settings.app_version,
                "database": "disconnected",
            },
        )

    return {
        "status": "ok",
        "version": settings.app_version,
        "database": "connected",
    }
