"""Health endpoint contract tests."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.main import app


async def test_health_check_returns_connected(client: AsyncClient) -> None:
    """API-11: a reachable database returns the canonical healthy payload."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "1.0.0",
        "database": "connected",
    }


async def test_health_check_returns_degraded_when_database_fails() -> None:
    """A database failure returns 503 without hiding the API health response."""
    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = SQLAlchemyError("database unavailable")

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        from httpx import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as test_client:
            response = await test_client.get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "version": "1.0.0",
        "database": "disconnected",
    }
