from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from app.db import get_session
from app.models import METERS_PER_MILE, Lap, Run, RunShoe, Shoe
from app.schemas import RunDetailOut, RunSummaryOut, run_detail, run_summary
from app.services.shoes import SegmentError, SegmentInput, replace_segments

router = APIRouter(prefix="/runs", tags=["runs"])


def _shoes(session: Session) -> dict[int, Shoe]:
    return {s.id: s for s in session.exec(select(Shoe))}


def _segments(session: Session, run_ids: list[int]) -> dict[int, list[RunShoe]]:
    out: dict[int, list[RunShoe]] = {rid: [] for rid in run_ids}
    if run_ids:
        for seg in session.exec(select(RunShoe).where(RunShoe.run_id.in_(run_ids)).order_by(RunShoe.id)):
            out[seg.run_id].append(seg)
    return out


class RunPage(BaseModel):
    items: list[RunSummaryOut]
    total: int


@router.get("", response_model=RunPage)
def list_runs(
    start: date | None = None,
    end: date | None = None,
    shoe_id: int | None = None,
    ids: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    query = select(Run)
    if start:
        query = query.where(Run.local_date >= start)
    if end:
        query = query.where(Run.local_date <= end)
    if shoe_id is not None:
        query = query.where(Run.id.in_(select(RunShoe.run_id).where(RunShoe.shoe_id == shoe_id)))
    if ids:
        query = query.where(Run.id.in_([int(i) for i in ids.split(",") if i.strip().isdigit()]))
    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    runs = list(session.exec(query.order_by(Run.start_local.desc()).offset(offset).limit(min(limit, 500))))
    segments = _segments(session, [r.id for r in runs])
    shoes = _shoes(session)
    return {"items": [run_summary(r, segments[r.id], shoes) for r in runs], "total": total}


def _get_run(session: Session, run_id: int) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/{run_id}", response_model=RunDetailOut)
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = _get_run(session, run_id)
    laps = list(session.exec(select(Lap).where(Lap.run_id == run.id)))
    return run_detail(run, _segments(session, [run.id])[run.id], _shoes(session), laps)


class SegmentIn(BaseModel):
    shoe_id: int
    miles: float | None = Field(default=None, gt=0)
    lap_from: int | None = None
    lap_to: int | None = None
    note: str | None = None


class SegmentsIn(BaseModel):
    segments: list[SegmentIn]


@router.put("/{run_id}/shoes", response_model=RunDetailOut)
def set_run_shoes(run_id: int, body: SegmentsIn, session: Session = Depends(get_session)):
    run = _get_run(session, run_id)
    inputs = [
        SegmentInput(
            shoe_id=s.shoe_id,
            distance_m=None if s.miles is None else s.miles * METERS_PER_MILE,
            lap_from=s.lap_from,
            lap_to=s.lap_to,
            note=s.note,
        )
        for s in body.segments
    ]
    try:
        replace_segments(session, run, inputs)
    except SegmentError as exc:
        raise HTTPException(422, str(exc)) from exc
    return get_run(run_id, session)
