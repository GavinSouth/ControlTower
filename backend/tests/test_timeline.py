"""The day-by-day timeline rule (pure function, no database)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from controltower.models import (
    Flight,
    Item,
    ItemStatus,
    LogEntry,
    LogKind,
    LogSource,
    Note,
    Stay,
    Trip,
    TripDay,
)
from controltower.timeline import Role, TimelineTooLongError, build_timeline

PACIFIC = ZoneInfo("America/Los_Angeles")
TOKYO = ZoneInfo("Asia/Tokyo")


def trip_of(*items: Item, **fields: object) -> Trip:
    return Trip(title="Japan", home_tz="Asia/Tokyo", items=list(items), **fields)


def hotel(check_in: int, check_out: int, **fields: object) -> Stay:
    return Stay(
        title=fields.pop("title", "Hotel X"),
        planned_start=datetime(2027, 4, check_in, 15, tzinfo=TOKYO),
        planned_end=datetime(2027, 4, check_out, 11, tzinfo=TOKYO),
        start_tz="Asia/Tokyo",
        **fields,
    )


def roles(trip: Trip) -> dict[date, list[tuple[str, Role]]]:
    return {
        d.local_date: [(listing.item.title, listing.role) for listing in d.listings]
        for d in build_timeline(trip).days
    }


def test_stay_is_stored_once_and_listed_on_every_day() -> None:
    assert roles(trip_of(hotel(6, 10))) == {
        date(2027, 4, 6): [("Hotel X", Role.STARTS)],
        date(2027, 4, 7): [("Hotel X", Role.CONTINUES)],
        date(2027, 4, 8): [("Hotel X", Role.CONTINUES)],
        date(2027, 4, 9): [("Hotel X", Role.CONTINUES)],
        date(2027, 4, 10): [("Hotel X", Role.ENDS)],
    }


def test_overnight_flight_uses_each_ends_own_zone() -> None:
    flight = Flight(
        title="UA 837",
        planned_start=datetime(2027, 4, 5, 11, 5, tzinfo=PACIFIC),
        planned_end=datetime(2027, 4, 6, 15, 25, tzinfo=TOKYO),
        start_tz="America/Los_Angeles",
        end_tz="Asia/Tokyo",
    )
    timeline = build_timeline(trip_of(flight))
    assert [(d.local_date, d.number) for d in timeline.days] == [
        (date(2027, 4, 5), 1),
        (date(2027, 4, 6), 2),
    ]
    assert [listing.role for d in timeline.days for listing in d.listings] == [
        Role.STARTS,
        Role.ENDS,
    ]


def test_day_order_continuing_first_then_by_relevant_time() -> None:
    lunch = Note(
        title="Lunch",
        planned_start=datetime(2027, 4, 8, 12, tzinfo=TOKYO),
        start_tz="Asia/Tokyo",
    )
    breakfast = Note(
        title="Breakfast",
        planned_start=datetime(2027, 4, 8, 8, tzinfo=TOKYO),
        start_tz="Asia/Tokyo",
    )
    # Hotel A checks out at 11:00 on the 8th, hotel B checks in at 15:00; C carries on.
    trip = trip_of(
        lunch,
        hotel(8, 10, title="Hotel B"),
        hotel(6, 8, title="Hotel A"),
        breakfast,
        hotel(6, 12, title="Hotel C"),
    )
    assert roles(trip)[date(2027, 4, 8)] == [
        ("Hotel C", Role.CONTINUES),
        ("Breakfast", Role.SINGLE),
        ("Hotel A", Role.ENDS),
        ("Lunch", Role.SINGLE),
        ("Hotel B", Role.STARTS),
    ]


def test_actual_times_move_an_item() -> None:
    late = hotel(6, 8)
    late.actual_start = datetime(2027, 4, 7, 1, 30, tzinfo=TOKYO)  # arrived after midnight
    days = roles(trip_of(late))
    assert days[date(2027, 4, 7)] == [("Hotel X", Role.STARTS)]
    assert date(2027, 4, 6) not in days  # nothing else made the 6th part of the trip


def test_untimed_items_are_unscheduled_and_empty_days_kept() -> None:
    idea = Note(title="Maybe: teamLab", status=ItemStatus.IDEA)
    trip = trip_of(idea, start_date=date(2027, 4, 6), end_date=date(2027, 4, 8))
    timeline = build_timeline(trip)
    assert [i.title for i in timeline.unscheduled] == ["Maybe: teamLab"]
    assert [d.local_date for d in timeline.days] == [
        date(2027, 4, 6),
        date(2027, 4, 7),
        date(2027, 4, 8),
    ]
    assert all(d.listings == [] for d in timeline.days)


def test_stored_dates_clip_items_and_roles_stay_true() -> None:
    # The stay began before the trip's stored start: on day 1 it "continues".
    trip = trip_of(hotel(4, 10), start_date=date(2027, 4, 6), end_date=date(2027, 4, 8))
    days = roles(trip)
    assert list(days) == [date(2027, 4, 6), date(2027, 4, 7), date(2027, 4, 8)]
    assert days[date(2027, 4, 6)] == [("Hotel X", Role.CONTINUES)]


def test_cancelled_items_listed_but_do_not_widen_the_range() -> None:
    cancelled = hotel(1, 20, title="Cancelled", status=ItemStatus.CANCELLED)
    days = roles(trip_of(hotel(6, 7), cancelled))
    assert list(days) == [date(2027, 4, 6), date(2027, 4, 7)]
    assert ("Cancelled", Role.CONTINUES) in days[date(2027, 4, 6)]


def test_log_entries_and_extras_land_on_their_local_days() -> None:
    trip = trip_of(hotel(6, 7))
    # 23:30 UTC on the 6th is 08:30 on the 7th in Tokyo.
    trip.log_entries = [
        LogEntry(
            occurred_at=datetime(2027, 4, 6, 23, 30, tzinfo=ZoneInfo("UTC")),
            tz="Asia/Tokyo",
            source=LogSource.MANUAL,
            kind=LogKind.NOTE,
            text="breakfast",
        ),
        LogEntry(
            occurred_at=datetime(2027, 4, 9, 9, 0, tzinfo=TOKYO),
            tz="Asia/Tokyo",
            source=LogSource.MANUAL,
            kind=LogKind.NOTE,
            text="extra day",
        ),
    ]
    trip.days = [TripDay(local_date=date(2027, 4, 6), title="Arrival", city="Tokyo")]
    timeline = build_timeline(trip)

    by_date = {d.local_date: d for d in timeline.days}
    assert [e.text for e in by_date[date(2027, 4, 7)].log] == ["breakfast"]
    assert timeline.last_day == date(2027, 4, 9)  # the log entry widened the range
    assert by_date[date(2027, 4, 8)].listings == []
    extras = by_date[date(2027, 4, 6)].extras
    assert extras is not None and extras.title == "Arrival"


def test_unscheduled_trip_has_no_days() -> None:
    timeline = build_timeline(trip_of(Note(title="Packing list")))
    assert (timeline.first_day, timeline.days) == (None, [])
    assert len(timeline.unscheduled) == 1


def test_absurd_range_is_refused() -> None:
    trip = trip_of(start_date=date(2027, 1, 1), end_date=date(2029, 1, 1))
    with pytest.raises(TimelineTooLongError):
        build_timeline(trip)
