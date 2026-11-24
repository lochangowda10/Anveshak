"""Initial empty migration.

Revision ID: 0000
Revises:
"""

from collections.abc import Sequence

revision: str = "0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the initial migration baseline."""


def downgrade() -> None:
    """Leave the database unchanged at the initial baseline."""
