from datetime import date, timedelta

import pytest

from app.services.mileage import bucket_weeks, range_start, week_start, weekly_series, with_rolling_average
from tests.factories import make_run


def test_week_starts_monday_and_sunday_belongs_to_previous_week():
    assert week_start(date(2026, 10, 12)) == date(2026, 10, 12)  # Monday
    assert week_start(date(2026, 10, 18)) == date(2026, 10, 12)  # Sunday
    assert week_start(date(2026, 10, 19)) == date(2026, 10, 19)  # next Monday


def test_sunday_night_run_counts_toward_that_week(session):
    sunday_night = make_run(session, date(2026, 10, 18), 5, hour=23)
    monday = make_run(session, date(2026, 10, 19), 3, hour=6)
    weeks = bucket_weeks([sunday_night, monday], date(2026, 10, 12), date(2026, 10, 19))
    assert [(w.start, round(w.miles, 2)) for w in weeks] == [(date(2026, 10, 12), 5.0), (date(2026, 10, 19), 3.0)]


def test_dst_change_week_is_still_seven_days(session):
    # US DST ended 2026-11-01 (a Sunday); local dates are what matter.
    runs = [make_run(session, date(2026, 10, 26), 4), make_run(session, date(2026, 11, 1), 6, hour=1)]
    weeks = bucket_weeks(runs, date(2026, 10, 26), date(2026, 11, 2))
    assert weeks[0].start == date(2026, 10, 26) and weeks[0].miles == pytest.approx(10)
    assert weeks[1].start == date(2026, 11, 2) and weeks[1].miles == 0


def test_empty_weeks_are_zero_filled(session):
    runs = [make_run(session, date(2026, 9, 1), 4), make_run(session, date(2026, 9, 29), 6)]
    weeks = bucket_weeks(runs, date(2026, 9, 1), date(2026, 9, 29))
    assert [round(w.miles) for w in weeks] == [4, 0, 0, 0, 6]
    assert weeks[0].runs == 1 and weeks[1].runs == 0


def test_rolling_average_uses_up_to_four_weeks(session):
    runs = [make_run(session, date(2026, 9, 7) + timedelta(weeks=i), m) for i, m in enumerate([10, 20, 30, 40, 50])]
    weeks = with_rolling_average(bucket_weeks(runs, date(2026, 9, 7), date(2026, 10, 5)))
    assert [round(w.rolling_avg, 2) for w in weeks] == [10, 15, 20, 25, 35]


def test_ranges():
    today = date(2026, 10, 17)  # Saturday; week starts 2026-10-12
    assert range_start("3m", today, None) == date(2026, 7, 20)  # 13 weeks incl. this one
    assert range_start("1y", today, None) == date(2025, 10, 20)
    assert range_start("ytd", today, None) == date(2025, 12, 29)  # week containing Jan 1
    assert range_start("all", today, date(2024, 3, 6)) == date(2024, 3, 4)
    with pytest.raises(ValueError):
        range_start("2w", today, None)


def test_weekly_series_has_one_entry_per_week_and_real_rolling_average(session):
    today = date(2026, 10, 17)
    for i in range(20):
        make_run(session, date(2026, 6, 1 + i) if i < 20 else today, 5)
    weeks, _ = weekly_series(session, "3m", today=today)
    assert len(weeks) == 13
    assert weeks[-1].start == date(2026, 10, 12)
