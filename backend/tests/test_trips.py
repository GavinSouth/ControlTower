"""Computed trip rules: date range and phase (no database needed)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from controltower.models import Flight, ItemStatus, Note, Stay, Trip
from controltower.trips import TripPhase, trip_date_range, trip_phase

TOKYO = ZoneInfo("Asia/Tokyo")


def trip_with(*items: Flight | Stay | Note, **fields: object) -> Trip:
    return Trip(title="t", home_tz="Asia/Tokyo", items=list(items), **fields)


def stay(day_from: int, day_to: int, **fields: object) -> Stay:
    return Stay(
        title="s",
        planned_start=datetime(2027, 4, day_from, 15, tzinfo=TOKYO),
        planned_end=datetime(2027, 4, day_to, 11, tzinfo=TOKYO),
        start_tz="Asia/Tokyo",
        **fields,
    )


def test_range_from_items_uses_local_days() -> None:
    # 07:00 on the 6th in Tokyo is 22:00 on the 5th in UTC: the local day (6th) counts.
    early = Note(title="n", planned_start=datetime(2027, 4, 6, 7, 0, tzinfo=TOKYO))
    trip = trip_with(stay(7, 10), early)
    assert trip_date_range(trip) == (date(2027, 4, 6), date(2027, 4, 10))


def test_stored_dates_win_and_cancelled_items_are_ignored() -> None:
    trip = trip_with(stay(7, 10), stay(1, 20, status=ItemStatus.CANCELLED))
    assert trip_date_range(trip) == (date(2027, 4, 7), date(2027, 4, 10))
    trip.start_date = date(2027, 4, 5)
    assert trip_date_range(trip) == (date(2027, 4, 5), date(2027, 4, 10))


def test_phase() -> None:
    trip = trip_with(stay(7, 10))
    assert trip_phase(trip, today=date(2027, 4, 6)) is TripPhase.UPCOMING
    assert trip_phase(trip, today=date(2027, 4, 7)) is TripPhase.CURRENT
    assert trip_phase(trip, today=date(2027, 4, 10)) is TripPhase.CURRENT
    assert trip_phase(trip, today=date(2027, 4, 11)) is TripPhase.PAST
    assert trip_phase(trip_with()) is TripPhase.UNSCHEDULED
