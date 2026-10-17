from datetime import date, timedelta

from sqlmodel import Session, select

from app.garmin.parse import PR_TYPES
from app.models import METERS_PER_MILE, PersonalRecord, Run
from app.services.mileage import bucket_weeks, week_start


def weekly_streaks(week_miles: list[tuple[date, float]], today: date) -> tuple[int, int]:
    """(current, longest) streak of consecutive weeks with at least one run.

    The current week doesn't break a streak until it's over, so a streak that
    ran through last week is still "current" on Monday morning.
    """
    longest = run = 0
    for _, miles in week_miles:
        run = run + 1 if miles > 0 else 0
        longest = max(longest, run)
    current = 0
    this_week = week_start(today)
    for start, miles in reversed(week_miles):
        if miles > 0:
            current += 1
        elif start != this_week:
            break
    return current, longest


def compute_records(session: Session, today: date | None = None) -> dict:
    today = today or date.today()
    runs = list(session.exec(select(Run).order_by(Run.local_date)))
    garmin_prs = [
        {
            "type_id": pr.type_id,
            "label": PR_TYPES.get(pr.type_id, str(pr.type_id)),
            "value": pr.value,
            "activity_id": pr.activity_id,
            "date": pr.record_date,
        }
        for pr in session.exec(select(PersonalRecord).order_by(PersonalRecord.type_id))
    ]
    if not runs:
        return {"garmin_prs": garmin_prs, "longest_run": None, "biggest_week": None,
                "current_streak_weeks": 0, "longest_streak_weeks": 0, "ytd": None, "totals": None}

    weeks = bucket_weeks(runs, runs[0].local_date, today)
    biggest = max(weeks, key=lambda w: w.miles)
    current, longest = weekly_streaks([(w.start, w.miles) for w in weeks], today)
    longest_run = max(runs, key=lambda r: r.distance_m)

    def miles_between(start: date, end: date) -> float:
        return sum(r.distance_m for r in runs if start <= r.local_date <= end) / METERS_PER_MILE

    jan1 = date(today.year, 1, 1)
    try:
        same_day_last_year = today.replace(year=today.year - 1)
    except ValueError:  # Feb 29
        same_day_last_year = today.replace(year=today.year - 1, day=28)

    return {
        "garmin_prs": garmin_prs,
        "longest_run": {
            "run_id": longest_run.id,
            "miles": longest_run.distance_m / METERS_PER_MILE,
            "date": longest_run.local_date,
            "name": longest_run.name,
        },
        "biggest_week": {"week_start": biggest.start, "miles": biggest.miles, "runs": biggest.runs},
        "current_streak_weeks": current,
        "longest_streak_weeks": longest,
        "ytd": {
            "this_year": miles_between(jan1, today),
            "last_year_to_date": miles_between(jan1.replace(year=today.year - 1), same_day_last_year),
            "last_year_total": miles_between(jan1.replace(year=today.year - 1), date(today.year - 1, 12, 31)),
            "cumulative": _cumulative_by_day(runs, today),
        },
        "totals": {
            "runs": len(runs),
            "miles": sum(r.distance_m for r in runs) / METERS_PER_MILE,
            "since": runs[0].local_date,
        },
    }


def _cumulative_by_day(runs: list[Run], today: date) -> list[dict]:
    """Cumulative miles by day-of-year for this year and last year (YTD chart)."""
    out = []
    for year in (today.year - 1, today.year):
        daily: dict[int, float] = {}
        for r in runs:
            if r.local_date.year == year:
                doy = r.local_date.timetuple().tm_yday
                daily[doy] = daily.get(doy, 0.0) + r.distance_m / METERS_PER_MILE
        last_day = today.timetuple().tm_yday if year == today.year else (date(year, 12, 31) - date(year, 1, 1)).days + 1
        total = 0.0
        for doy in range(1, last_day + 1):
            total += daily.get(doy, 0.0)
            if doy % 7 == 1 or doy == last_day:
                out.append({"year": year, "day_of_year": doy, "date": date(year, 1, 1) + timedelta(days=doy - 1), "miles": round(total, 2)})
    return out
