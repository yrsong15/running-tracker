"""Weekly mileage. Weeks run Monday through Sunday in the local time of each run."""

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlmodel import Session, select

from app.models import METERS_PER_MILE, Run

RANGES = {"3m": 13, "6m": 26, "1y": 52}
ROLLING_WEEKS = 4


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


@dataclass
class Week:
    start: date
    miles: float = 0.0
    runs: int = 0
    longest_miles: float = 0.0
    rolling_avg: float = 0.0
    run_ids: list[int] = field(default_factory=list)


def range_start(range_key: str, today: date, first_run: date | None) -> date:
    this_week = week_start(today)
    if range_key in RANGES:
        return this_week - timedelta(weeks=RANGES[range_key] - 1)
    if range_key == "ytd":
        return week_start(date(today.year, 1, 1))
    if range_key == "all":
        return week_start(first_run) if first_run else this_week
    raise ValueError(f"Unknown range {range_key!r}; use 3m, 6m, 1y, ytd or all")


def bucket_weeks(runs: list[Run], start: date, end: date) -> list[Week]:
    """Zero-filled weekly totals from `start`'s week through `end`'s week."""
    start, end = week_start(start), week_start(end)
    weeks: dict[date, Week] = {}
    cursor = start
    while cursor <= end:
        weeks[cursor] = Week(start=cursor)
        cursor += timedelta(weeks=1)
    for run in runs:
        week = weeks.get(week_start(run.local_date))
        if week is None:
            continue
        miles = run.distance_m / METERS_PER_MILE
        week.miles += miles
        week.runs += 1
        week.longest_miles = max(week.longest_miles, miles)
        week.run_ids.append(run.id)
    return list(weeks.values())


def with_rolling_average(weeks: list[Week]) -> list[Week]:
    for i, week in enumerate(weeks):
        window = weeks[max(0, i - ROLLING_WEEKS + 1) : i + 1]
        week.rolling_avg = sum(w.miles for w in window) / len(window)
    return weeks


def weekly_series(session: Session, range_key: str, today: date | None = None) -> list[Week]:
    today = today or date.today()
    first = session.exec(select(Run.local_date).order_by(Run.local_date)).first()
    start = range_start(range_key, today, first)
    # Read a few extra weeks so the first visible week's rolling average is real.
    lead_in = start - timedelta(weeks=ROLLING_WEEKS - 1)
    runs = list(session.exec(select(Run).where(Run.local_date >= lead_in, Run.local_date <= today)))
    weeks = with_rolling_average(bucket_weeks(runs, lead_in, today))
    return [w for w in weeks if w.start >= start]
