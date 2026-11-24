"""Configuration and startup script tests."""

from app.core.config import Settings
from app.scripts.seed_labels import main as seed_labels


def test_cors_origins_are_trimmed() -> None:
    """Comma-separated CORS configuration becomes a clean origin list."""
    settings = Settings(
        _env_file=None,
        cors_origins="http://localhost:5173, http://localhost:3000,",
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


async def test_seed_labels_entrypoint_is_idempotent_scaffold() -> None:
    """The startup hook succeeds before attribution models are introduced."""
    assert await seed_labels() is None
