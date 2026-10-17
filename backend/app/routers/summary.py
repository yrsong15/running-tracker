from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import DailyMetrics, Run, Shoe
from app.routers.shoes import shoe_out
from app.services.mileage import bucket_weeks, weekly_series, week_start
from app.services.shoes import logged_meters_by_shoe

router = APIRouter(prefix="/summary", tags=["summary"])


def _week_dict(w) -> dict:
    return {
        "week_start": w.start,
        "week_end": w.start + timedelta(days=6),
        "miles": round(w.miles, 2),
        "runs": w.runs,
        "longest_miles": round(w.longest_miles, 2),
        "rolling_avg": round(w.rolling_avg, 2),
        "run_ids": w.run_ids,
    }


@router.get("/weekly")
def weekly(range: str = "3m", session: Session = Depends(get_session)):  # noqa: A002
    try:
        weeks = weekly_series(session, range)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"range": range, "weeks": [_week_dict(w) for w in weeks]}


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    today = date.today()
    this_week = week_start(today)
    last_week = this_week - timedelta(weeks=1)
    runs = list(session.exec(select(Run).where(Run.local_date >= last_week)))
    last, this = bucket_weeks(runs, last_week, today)

    logged = logged_meters_by_shoe(session)
    active = [shoe_out(session, s, logged) for s in session.exec(select(Shoe).where(Shoe.retired_at.is_(None)))]
    latest_metrics = session.exec(select(DailyMetrics).order_by(DailyMetrics.day.desc())).first()
    return {
        "this_week": _week_dict(this),
        "last_week": _week_dict(last),
        "shoe_alerts": [s for s in active if s.wear != "ok"],
        "today": latest_metrics.model_dump() if latest_metrics else None,
    }
