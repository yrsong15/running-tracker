"""Postgres-specific column rules that SQLite-backed tests can't catch on their own."""

from sqlalchemy import BigInteger, DateTime
from sqlmodel import SQLModel

import app.models  # noqa: F401


def _columns():
    for table in SQLModel.metadata.sorted_tables:
        yield from table.columns


def test_garmin_ids_are_64_bit():
    # Real Garmin activity IDs (e.g. 21_000_000_000) overflow a 32-bit INTEGER.
    tables = SQLModel.metadata.tables
    assert isinstance(tables["runs"].c.garmin_activity_id.type, BigInteger)
    assert isinstance(tables["personal_records"].c.activity_id.type, BigInteger)


def test_timestamps_are_timezone_naive():
    # The app writes naive datetimes (UTC, and start_local as wall-clock time);
    # TIMESTAMPTZ would hand back aware values and break comparisons.
    aware = [f"{c.table.name}.{c.name}" for c in _columns() if isinstance(c.type, DateTime) and c.type.timezone]
    assert aware == []
