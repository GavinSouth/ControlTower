"""Create demo trips to explore the app with (opt-in; safe to re-run).

    uv run python -m controltower.demo

"Japan (demo)" is upcoming: every item kind, an overnight flight across zones, a
multi-night stay, a delayed departure (actual vs planned), a log entry, day extras, and
an unscheduled idea.

"Lisbon (demo)" is already past (May 2025) for the past trip record (F3.4): day
summaries and log written as a journal, a skipped item, costs in two currencies, and
feedback on about half the items, but no trip reflection yet, so the app shows the
"How was it?" prompt and you can try reflecting.
"""

from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from controltower.db import get_or_create_owner, make_engine, make_session_factory
from controltower.models import (
    Activity,
    Flight,
    ItemFeedback,
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
    Verdict,
)

DEMO_TITLE = "Japan (demo)"
PAST_DEMO_TITLE = "Lisbon (demo)"
LA = ZoneInfo("America/Los_Angeles")
TOKYO = ZoneInfo("Asia/Tokyo")
LISBON = ZoneInfo("Europe/Lisbon")


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


def _lis(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 5, day, hour, minute, tzinfo=LISBON)


def create_past_demo_trip(session: Session) -> Trip | None:
    """Add the past Lisbon trip unless it already exists. Returns it, or None if it existed."""
    owner = get_or_create_owner(session)
    exists = session.scalar(
        select(Trip).where(Trip.owner_id == owner.id, Trip.title == PAST_DEMO_TITLE)
    )
    if exists:
        return None

    sfo = Place(
        name="SFO", city="San Francisco", country="US", tz="America/Los_Angeles", iata_code="SFO"
    )
    lis = Place(
        name="Lisbon Airport", city="Lisbon", country="PT", tz="Europe/Lisbon", iata_code="LIS"
    )
    hotel = Place(
        name="Memmo Alfama", city="Lisbon", country="PT", lat=38.711, lon=-9.130, tz="Europe/Lisbon"
    )
    belem = Place(
        name="Pastéis de Belém",
        city="Lisbon",
        country="PT",
        lat=38.697,
        lon=-9.203,
        tz="Europe/Lisbon",
    )
    pena = Place(
        name="Pena Palace", city="Sintra", country="PT", lat=38.788, lon=-9.391, tz="Europe/Lisbon"
    )
    market = Place(
        name="Time Out Market",
        city="Lisbon",
        country="PT",
        lat=38.707,
        lon=-9.146,
        tz="Europe/Lisbon",
    )

    trip = Trip(
        owner=owner,
        title=PAST_DEMO_TITLE,
        location="Lisbon & Sintra, Portugal",
        start_date=date(2025, 5, 10),
        end_date=date(2025, 5, 15),
        home_tz="Europe/Lisbon",
    )
    flight_out = Flight(
        title="SFO → LIS",
        status=ItemStatus.DONE,
        planned_start=datetime(2025, 5, 9, 15, 0, tzinfo=LA),
        planned_end=_lis(10, 10, 40),
        start_tz="America/Los_Angeles",
        end_tz="Europe/Lisbon",
        place=sfo,
        to_place=lis,
        airline="TP",
        flight_number="238",
        cost_amount=Decimal("890"),
        cost_currency="USD",
    )
    stay = Stay(
        title="Memmo Alfama",
        status=ItemStatus.DONE,
        planned_start=_lis(10, 15),
        planned_end=_lis(15, 11),
        start_tz="Europe/Lisbon",
        place=hotel,
        property_name="Memmo Alfama",
        cost_amount=Decimal("1150"),
        cost_currency="EUR",
    )
    tram = Transport(
        title="Tram 28 across town",
        status=ItemStatus.DONE,
        planned_start=_lis(11, 9, 30),
        planned_end=_lis(11, 10, 15),
        start_tz="Europe/Lisbon",
        mode=TransportMode.OTHER,
        carrier="Carris",
        cost_amount=Decimal("3"),
        cost_currency="EUR",
    )
    tarts = Activity(
        title="Pastéis de Belém",
        status=ItemStatus.DONE,
        planned_start=_lis(11, 11),
        start_tz="Europe/Lisbon",
        place=belem,
        category="food",
        cost_amount=Decimal("8.40"),
        cost_currency="EUR",
    )
    museum = Activity(
        title="Coach Museum",
        status=ItemStatus.SKIPPED,
        planned_start=_lis(11, 14),
        start_tz="Europe/Lisbon",
        category="sight",
    )
    palace = Activity(
        title="Pena Palace",
        status=ItemStatus.DONE,
        planned_start=_lis(12, 10),
        planned_end=_lis(12, 14),
        start_tz="Europe/Lisbon",
        place=pena,
        category="sight",
        cost_amount=Decimal("20"),
        cost_currency="EUR",
    )
    food_hall = Activity(
        title="Dinner at Time Out Market",
        status=ItemStatus.DONE,
        planned_start=_lis(13, 20),
        start_tz="Europe/Lisbon",
        place=market,
        category="food",
        cost_amount=Decimal("46"),
        cost_currency="EUR",
    )
    fado = Activity(
        title="Fado in Alfama",
        status=ItemStatus.DONE,
        planned_start=_lis(14, 21),
        start_tz="Europe/Lisbon",
        place=hotel,
        category="event",
        cost_amount=Decimal("35"),
        cost_currency="EUR",
    )
    flight_home = Flight(
        title="LIS → SFO",
        status=ItemStatus.DONE,
        planned_start=_lis(15, 13, 0),
        planned_end=datetime(2025, 5, 15, 16, 35, tzinfo=LA),
        start_tz="Europe/Lisbon",
        end_tz="America/Los_Angeles",
        place=lis,
        to_place=sfo,
        airline="TP",
        flight_number="237",
    )
    trip.items = [
        flight_out,
        stay,
        tram,
        tarts,
        museum,
        palace,
        food_hall,
        fado,
        flight_home,
    ]
    trip.days = [
        TripDay(
            local_date=date(2025, 5, 10),
            title="Arrival",
            city="Lisbon",
            summary="Landed sleepy, dropped bags in Alfama, and wandered downhill "
            "to the river for the first sunset.",
        ),
        TripDay(
            local_date=date(2025, 5, 11),
            title="Belém",
            city="Lisbon",
            summary="Tram 28 out west, warm custard tarts, and a long walk along the "
            "water instead of the museum.",
        ),
        TripDay(
            local_date=date(2025, 5, 12),
            title="Sintra",
            city="Sintra",
            summary="Fog lifted just as we reached Pena. Worth the early train.",
        ),
        TripDay(
            local_date=date(2025, 5, 14),
            title="Last night",
            city="Lisbon",
            summary="Fado in a tiny room around the corner from the hotel.",
        ),
    ]
    trip.log_entries = [
        LogEntry(
            occurred_at=_lis(10, 20, 45),
            tz="Europe/Lisbon",
            source=LogSource.MANUAL,
            kind=LogKind.NOTE,
            text="Sunset from Miradouro de Santa Luzia.",
        ),
        LogEntry(
            occurred_at=_lis(11, 13, 30),
            tz="Europe/Lisbon",
            source=LogSource.MANUAL,
            kind=LogKind.NOTE,
            text="Skipped the museum: too sunny to be inside.",
            item=museum,
        ),
        LogEntry(
            occurred_at=_lis(12, 10, 5),
            tz="Europe/Lisbon",
            source=LogSource.MANUAL,
            kind=LogKind.ARRIVAL,
            text="Made it to Pena before the crowds.",
            item=palace,
            place=pena,
        ),
    ]
    session.add(trip)
    session.flush()  # assign item ids for the feedback rows

    # About half the items rated, so the "still need feedback" prompt has work left.
    session.add_all(
        [
            ItemFeedback(
                item_id=tarts.id,
                user_id=owner.id,
                verdict=Verdict.UP,
                favourite=True,
                review="Warm from the oven. Worth the queue.",
            ),
            ItemFeedback(item_id=palace.id, user_id=owner.id, verdict=Verdict.UP, favourite=True),
            ItemFeedback(item_id=stay.id, user_id=owner.id, verdict=Verdict.UP),
            ItemFeedback(
                item_id=food_hall.id,
                user_id=owner.id,
                verdict=Verdict.DOWN,
                review="Loud and crowded; fine, not special.",
            ),
        ]
    )
    session.commit()
    return trip


if __name__ == "__main__":
    with make_session_factory(make_engine())() as session:
        for title, create in (
            (DEMO_TITLE, create_demo_trip),
            (PAST_DEMO_TITLE, create_past_demo_trip),
        ):
            print(f"Created “{title}”." if create(session) else f"“{title}” already exists.")
