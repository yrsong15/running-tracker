from datetime import date

import pytest

from app.models import METERS_PER_MILE
from app.services.shoes import (
    SegmentError,
    SegmentInput,
    apply_default_shoe,
    logged_meters_by_shoe,
    replace_segments,
    shoe_miles,
    wear_level,
)
from tests.factories import make_run, make_shoe

MI = METERS_PER_MILE


def test_split_run_across_two_shoes(session):
    trainer, spikes = make_shoe(session, "Trainer"), make_shoe(session, "Spikes")
    run = make_run(session, date(2026, 10, 14), 6)
    replace_segments(session, run, [SegmentInput(trainer.id, 2 * MI), SegmentInput(spikes.id, 4 * MI)])
    logged = logged_meters_by_shoe(session)
    assert logged[trainer.id] / MI == pytest.approx(2)
    assert logged[spikes.id] / MI == pytest.approx(4)


def test_segments_cannot_exceed_run_distance(session):
    shoe = make_shoe(session)
    run = make_run(session, date(2026, 10, 14), 6)
    with pytest.raises(SegmentError, match="add up to 7.00 mi"):
        replace_segments(session, run, [SegmentInput(shoe.id, 3 * MI), SegmentInput(shoe.id, 4 * MI)])


def test_small_overshoot_within_tolerance_is_allowed(session):
    shoe = make_shoe(session)
    run = make_run(session, date(2026, 10, 14), 5.98)
    replace_segments(session, run, [SegmentInput(shoe.id, 6.0 * MI)])


def test_partial_assignment_leaves_unassigned_miles(logged_in, session):
    shoe = make_shoe(session)
    run = make_run(session, date(2026, 10, 14), 6)
    res = logged_in.put(f"/api/runs/{run.id}/shoes", json={"segments": [{"shoe_id": shoe.id, "miles": 4}]})
    assert res.status_code == 200
    assert res.json()["unassigned_miles"] == pytest.approx(2)


def test_lap_range_fills_distance(session):
    trainer, spikes = make_shoe(session, "Trainer"), make_shoe(session, "Spikes")
    run = make_run(session, date(2026, 10, 14), 6, laps=[1, 1, 1, 1, 1, 1])
    replace_segments(session, run, [SegmentInput(trainer.id, lap_from=1, lap_to=2), SegmentInput(spikes.id, lap_from=3, lap_to=6)])
    logged = logged_meters_by_shoe(session)
    assert logged[trainer.id] / MI == pytest.approx(2)
    assert logged[spikes.id] / MI == pytest.approx(4)
    with pytest.raises(SegmentError, match="no lap 7"):
        replace_segments(session, run, [SegmentInput(trainer.id, lap_from=6, lap_to=7)])


def test_replacing_segments_removes_old_ones(session):
    a, b = make_shoe(session, "A"), make_shoe(session, "B")
    run = make_run(session, date(2026, 10, 14), 5)
    replace_segments(session, run, [SegmentInput(a.id, 5 * MI)])
    replace_segments(session, run, [SegmentInput(b.id, 5 * MI)])
    assert set(logged_meters_by_shoe(session)) == {b.id}


def test_shoe_total_includes_starting_miles():
    from app.models import Shoe

    shoe = Shoe(name="Old", start_miles=120)
    assert shoe_miles(shoe, 30 * MI) == pytest.approx(150)


def test_wear_levels():
    assert wear_level(100, 400) == "ok"
    assert wear_level(340, 400) == "warn"
    assert wear_level(400, 400) == "over"


def test_default_shoe_prefers_category_match(session):
    make_shoe(session, "Daily", is_default=True)
    trail = make_shoe(session, "Trail", default_for_category="trail")
    make_shoe(session, "Retired trail", default_for_category="trail", retired_at=date(2026, 1, 1))
    run = make_run(session, date(2026, 10, 14), 8, category="trail")
    apply_default_shoe(session, run)
    session.commit()
    assert logged_meters_by_shoe(session) == {trail.id: pytest.approx(8 * MI)}


def test_only_one_overall_default(logged_in):
    first = logged_in.post("/api/shoes", json={"name": "A", "is_default": True}).json()
    logged_in.post("/api/shoes", json={"name": "B", "is_default": True})
    shoes = {s["name"]: s for s in logged_in.get("/api/shoes").json()}
    assert shoes["B"]["is_default"] and not shoes["A"]["is_default"]
    retired = logged_in.post(f"/api/shoes/{first['id']}/retire").json()
    assert retired["retired_at"] is not None
