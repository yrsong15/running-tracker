"""add sport to runs

Rides are imported into the runs table alongside runs; every existing row is a run.

Revision ID: 5e2a9c7d1f30
Revises: 3c1d2e4f5a6b
Create Date: 2026-10-22 23:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '5e2a9c7d1f30'
down_revision: Union[str, Sequence[str], None] = '3c1d2e4f5a6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('runs') as batch:
        batch.add_column(sa.Column('sport', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='run'))
        batch.create_index(batch.f('ix_runs_sport'), ['sport'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('runs') as batch:
        batch.drop_index(batch.f('ix_runs_sport'))
        batch.drop_column('sport')
