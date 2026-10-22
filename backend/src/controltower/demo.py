"""Create a demo trip to explore the app with (opt-in; safe to re-run).

    uv run python -m controltower.demo

Covers every item kind, an overnight flight across zones, a multi-night stay, a delayed
departure (actual vs planned), a log entry, day extras, and an unscheduled idea.
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from controltower.db import get_or_create_owner, make_engine, make_session_factory
from controltower.models import (
    Activity,
    Flight,
    ItemStatus,
    LogEntry,
    LogKind,
    LogSource,
    Note,
    Place,
    Stay,
    Transport,
    TransportMode,
    Trip,
    TripDay,
)

DEMO_TITLE = "Japan (demo)"
LA = ZoneInfo("America/Los_Angeles")
TOKYO = ZoneInfo("Asia/Tokyo")


def create_demo_trip(session: Session) -> Trip | None:
    """Add the demo trip unless it already exists. Returns it, or None if it existed."""
    owner = get_or_create_owner(session)
    exists = session.scalar(select(Trip).where(Trip.owner_id == owner.id, Trip.title == DEMO_TITLE))
    if exists:
        return None

    sfo = Place(
        name="SFO", city="San Francisco", country="US", tz="America/Los_Angeles", iata_code="SFO"
    )
    hnd = Place(name="Haneda", city="Tokyo", country="JP", tz="Asia/Tokyo", iata_code="HND")
    hotel = Place(name="Hotel Gracery Shinjuku", city="Tokyo", country="JP", tz="Asia/Tokyo")
    market = Place(name="Tsukiji Outer Market", city="Tokyo", country="JP", tz="Asia/Tokyo")

    trip = Trip(
        owner=owner,
        title=DEMO_TITLE,
        location="Tokyo & Kyoto, Japan",
        home_tz="Asia/Tokyo",
        notes="Cherry blossom week.",
    )
    trip.items = [
        Flight(
            title="SFO → HND",
            status=ItemStatus.BOOKED,
            planned_start=datetime(2027, 4, 5, 11, 5, tzinfo=LA),
            planned_end=datetime(2027, 4, 6, 15, 25, tzinfo=TOKYO),
            actual_start=datetime(2027, 4, 5, 11, 52, tzinfo=LA),  # left 47 min late
            start_tz="America/Los_Angeles",
            end_tz="Asia/Tokyo",
            place=sfo,
            to_place=hnd,
            airline="UA",
            flight_number="837",
            seat="34K",
            confirmation_code="K7Q2ZP",
        ),
        Transport(
            title="Limousine bus to Shinjuku",
            planned_start=datetime(2027, 4, 6, 16, 30, tzinfo=TOKYO),
            planned_end=datetime(2027, 4, 6, 17, 40, tzinfo=TOKYO),
            start_tz="Asia/Tokyo",
            place=hnd,
            to_place=hotel,
            mode=TransportMode.BUS,
            carrier="Airport Limousine",
        ),
        Stay(
            title="Hotel Gracery",
            status=ItemStatus.BOOKED,
            planned_start=datetime(2027, 4, 6, 18, 0, tzinfo=TOKYO),
            planned_end=datetime(2027, 4, 9, 11, 0, tzinfo=TOKYO),
            start_tz="Asia/Tokyo",
            place=hotel,
            property_name="Hotel Gracery Shinjuku",
            check_in_after=time(15),
            check_out_before=time(11),
        ),
        Activity(
            title="Breakfast at Tsukiji",
            planned_start=datetime(2027, 4, 7, 8, 0, tzinfo=TOKYO),
            planned_end=datetime(2027, 4, 7, 10, 0, tzinfo=TOKYO),
            start_tz="Asia/Tokyo",
            place=market,
            category="food",
        ),
        Note(title="Maybe: teamLab Planets", status=ItemStatus.IDEA),
    ]
    trip.days = [TripDay(local_date=date(2027, 4, 6), title="Arrival", city="Tokyo")]
    trip.log_entries = [
        LogEntry(
            occurred_at=datetime(2027, 4, 6, 18, 20, tzinfo=TOKYO),
            tz="Asia/Tokyo",
            source=LogSource.MANUAL,
            kind=LogKind.CHECK_IN,
            text="Checked in, room on the 20th floor.",
            item=trip.items[2],
            place=hotel,
        )
    ]
    session.add(trip)
    session.commit()
    return trip


if __name__ == "__main__":
    with make_session_factory(make_engine())() as session:
        created = create_demo_trip(session)
    print(f"Created “{DEMO_TITLE}”." if created else f"“{DEMO_TITLE}” already exists.")
