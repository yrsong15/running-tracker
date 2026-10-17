from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import DailyMetrics, Run
from app.services.mileage import range_start

router = APIRouter(prefix="/metrics", tags=["metrics"])

FITNESS = ["vo2max", "resting_hr", "race_5k_s", "race_10k_s", "race_half_s", "race_full_s", "lt_hr", "lt_pace_s_per_mile"]
TRAINING = ["acute_load", "chronic_load", "acwr", "readiness_score", "readiness_level",
            "hrv_last_night", "hrv_weekly_avg", "hrv_status", "training_status"]


def _series(session: Session, range_key: str, fields: list[str]) -> list[dict]:
    first = session.exec(select(DailyMetrics.day).order_by(DailyMetrics.day)).first()
    try:
        start = range_start(range_key, date.today(), first)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    rows = session.exec(select(DailyMetrics).where(DailyMetrics.day >= start).order_by(DailyMetrics.day))
    out = []
    for row in rows:
        values = {f: getattr(row, f) for f in fields}
        if any(v is not None for v in values.values()):
            out.append({"day": row.day, **values})
    return out


@router.get("/fitness")
def fitness(range: str = "6m", session: Session = Depends(get_session)):  # noqa: A002
    series = _series(session, range, FITNESS)
    latest = {f: next((d[f] for d in reversed(series) if d[f] is not None), None) for f in FITNESS}
    return {"range": range, "series": series, "latest": latest}


@router.get("/training")
def training(range: str = "3m", session: Session = Depends(get_session)):  # noqa: A002
    series = _series(session, range, TRAINING)
    latest = {f: next((d[f] for d in reversed(series) if d[f] is not None), None) for f in TRAINING}
    first = series[0]["day"] if series else date.today()
    loads = session.exec(select(Run.local_date, Run.training_load).where(Run.local_date >= first))
    daily_load: dict[date, float] = {}
    for day, load in loads:
        daily_load[day] = daily_load.get(day, 0.0) + (load or 0.0)
    return {
        "range": range,
        "series": series,
        "latest": latest,
        "run_load": [{"day": d, "load": round(v, 1)} for d, v in sorted(daily_load.items())],
    }
