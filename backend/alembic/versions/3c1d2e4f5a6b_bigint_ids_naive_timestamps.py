"""bigint Garmin ids, timezone-naive timestamps

Garmin activity IDs overflow 32-bit INTEGER, and the initial migration created
timestamps as TIMESTAMPTZ while the app stores naive values (UTC, plus
start_local as wall-clock time where the run happened).

Revision ID: 3c1d2e4f5a6b
Revises: 7be19b8f807b
Create Date: 2026-10-22 21:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3c1d2e4f5a6b'
down_revision: Union[str, Sequence[str], None] = '7be19b8f807b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BIGINT_COLUMNS = [("runs", "garmin_activity_id"), ("personal_records", "activity_id")]
TIMESTAMP_COLUMNS = [
    ("garmin_auth", "updated_at"),
    ("runs", "start_utc"),
    ("runs", "start_local"),
    ("shoes", "created_at"),
    ("sync_state", "last_sync_at"),
    ("sync_state", "started_at"),
    ("sync_state", "last_activity_start"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite has no fixed integer width or time zone storage; nothing to change.
        return
    for table, column in BIGINT_COLUMNS:
        op.alter_column(table, column, type_=sa.BigInteger(), existing_type=sa.Integer())
    for table, column in TIMESTAMP_COLUMNS:
        # Values were written as naive datetimes into TIMESTAMPTZ under a UTC session,
        # so reading them back at UTC recovers exactly what the app wrote.
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            postgresql_using=f'"{column}" AT TIME ZONE \'UTC\'',
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            postgresql_using=f'"{column}" AT TIME ZONE \'UTC\'',
        )
    for table, column in BIGINT_COLUMNS:
        op.alter_column(table, column, type_=sa.Integer(), existing_type=sa.BigInteger())
