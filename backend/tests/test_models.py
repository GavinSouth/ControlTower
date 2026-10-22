"""Behaviour of the F2.1 data model (docs/ARCHITECTURE.md)."""

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session, sessionmaker

from controltower.db import get_or_create_owner
from controltower.models import (
    Activity,
    Flight,
    Item,
    ItemKind,
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

PACIFIC = ZoneInfo("America/Los_Angeles")
TOKYO = ZoneInfo("Asia/Tokyo")


def make_trip(session: Session) -> Trip:
    trip = Trip(owner=get_or_create_owner(session), title="Japan", home_tz="America/Los_Angeles")
    session.add(trip)
    return trip


def count(session: Session, table: str) -> int:
    return session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def test_owner_seed_is_idempotent(session: Session) -> None:
    first = get_or_create_owner(session)
    second = get_or_create_owner(session)
    assert first.id == second.id
    assert session.scalar(select(func.count()).select_from(type(first))) == 1


def test_every_item_kind_round_trips_polymorphically(
    session: Session, session_factory: sessionmaker[Session]
) -> None:
    trip = make_trip(session)
    sfo = Place(name="SFO", tz="America/Los_Angeles", iata_code="SFO")
    hnd = Place(name="Haneda", tz="Asia/Tokyo", iata_code="HND")
    trip.items = [
        Flight(title="SFO → HND", airline="UA", flight_number="837", place=sfo, to_place=hnd),
        Stay(title="Hotel X", property_name="Hotel X", check_in_after=time(15)),
        Transport(title="Monorail", mode=TransportMode.METRO),
        Activity(title="Tsukiji", category="food"),
        Note(title="Buy a Suica card"),
    ]
    session.commit()

    with session_factory() as fresh:  # new session: nothing cached, all loaded from the DB
        items = fresh.scalars(select(Item).order_by(Item.title)).all()
        assert {type(i) for i in items} == {Flight, Stay, Transport, Activity, Note}
        flight = next(i for i in items if isinstance(i, Flight))
        assert flight.kind is ItemKind.FLIGHT
        assert (flight.airline, flight.flight_number) == ("UA", "837")
        assert flight.place is not None and flight.place.iata_code == "SFO"
        assert flight.to_place is not None and flight.to_place.tz == "Asia/Tokyo"
        assert all(i.status is ItemStatus.PLANNED for i in items)

    # Notes have no detail table; the other kinds each have one row in theirs.
    assert count(session, "flight_detail") == 1
    assert count(session, "item") == 5


def test_times_are_stored_utc_and_keep_both_zones(
    session: Session, session_factory: sessionmaker[Session]
) -> None:
    trip = make_trip(session)
    depart = datetime(2027, 4, 5, 11, 5, tzinfo=PACIFIC)
    arrive = datetime(2027, 4, 6, 15, 25, tzinfo=TOKYO)
    trip.items.append(
        Flight(
            title="UA 837",
            planned_start=depart,
            planned_end=arrive,
            start_tz="America/Los_Angeles",
            end_tz="Asia/Tokyo",
        )
    )
    session.commit()

    with session_factory() as fresh:
        flight = fresh.scalars(select(Flight)).one()
        assert flight.planned_start == depart  # same instant...
        assert flight.planned_start is not None and flight.planned_start.tzinfo == UTC  # ...in UTC
        assert flight.planned_end is not None
        # The stored zone recovers the local wall-clock day the flight lands on.
        local_arrival = flight.planned_end.astimezone(ZoneInfo(flight.effective_end_tz or ""))
        assert local_arrival.date() == date(2027, 4, 6)


def test_naive_datetime_is_rejected(session: Session) -> None:
    trip = make_trip(session)
    trip.items.append(Note(title="no zone", planned_start=datetime(2027, 4, 5, 9, 0)))
    with pytest.raises(StatementError, match="naive datetime"):
        session.commit()


def test_unknown_time_zone_is_rejected(session: Session) -> None:
    session.add(Place(name="Atlantis", tz="Ocean/Atlantis"))
    with pytest.raises(StatementError, match="unknown time zone"):
        session.commit()


def test_money_is_exact(session: Session, session_factory: sessionmaker[Session]) -> None:
    trip = make_trip(session)
    trip.items.append(Stay(title="Hotel X", cost_amount=Decimal("0.1") * 3, cost_currency="USD"))
    session.commit()
    with session_factory() as fresh:
        assert fresh.scalars(select(Stay)).one().cost_amount == Decimal("0.3")  # float: 0.30000…4


def test_effective_times_prefer_actual() -> None:
    planned = datetime(2027, 4, 5, 18, 0, tzinfo=UTC)
    actual = datetime(2027, 4, 5, 18, 47, tzinfo=UTC)
    flight = Flight(title="delayed", planned_start=planned, start_tz="UTC")
    assert flight.effective_start == planned
    flight.actual_start = actual
    assert flight.effective_start == actual
    assert flight.effective_end_tz == "UTC"  # falls back to start_tz


def test_enums_are_stored_as_their_values(session: Session) -> None:
    trip = make_trip(session)
    trip.items.append(Activity(title="Museum", status=ItemStatus.IN_PROGRESS))
    session.commit()
    row = session.execute(text("SELECT kind, status FROM item")).one()
    assert tuple(row) == ("activity", "in_progress")


def test_deleting_a_trip_cascades_but_keeps_places(session: Session) -> None:
    trip = make_trip(session)
    hotel = Place(name="Hotel X", tz="Asia/Tokyo")
    stay = Stay(title="Hotel X", place=hotel)
    trip.items.append(stay)
    trip.days.append(TripDay(local_date=date(2027, 4, 6), title="Arrival"))
    trip.log_entries.append(
        LogEntry(
            occurred_at=datetime(2027, 4, 6, 7, 0, tzinfo=UTC),
            tz="Asia/Tokyo",
            source=LogSource.MANUAL,
            kind=LogKind.CHECK_IN,
            item=stay,
            place=hotel,
        )
    )
    session.commit()

    # Raw SQL delete, so this proves the *database* cascades (foreign keys are on).
    session.execute(text("DELETE FROM trip"))
    session.commit()
    for table in ("item", "stay_detail", "trip_day", "log_entry"):
        assert count(session, table) == 0, table
    assert count(session, "place") == 1


def test_deleting_an_item_unlinks_its_log_entries(session: Session) -> None:
    trip = make_trip(session)
    note = Note(title="Lunch")
    trip.items.append(note)
    entry = LogEntry(
        occurred_at=datetime(2027, 4, 6, 3, 0, tzinfo=UTC),
        tz="Asia/Tokyo",
        source=LogSource.AGENT,
        kind=LogKind.NOTE,
        text="Had ramen",
        item=note,
        raw={"model": "test"},
    )
    trip.log_entries.append(entry)
    session.commit()

    session.execute(text("DELETE FROM item"))
    session.commit()
    session.expire_all()
    assert entry.item_id is None  # the minutes survive; only the link is cleared
    assert entry.raw == {"model": "test"}


def test_foreign_keys_are_enforced(session: Session) -> None:
    session.add(Note(trip_id=uuid.uuid4(), title="orphan"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_one_trip_day_row_per_date(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as s1:
        trip = make_trip(s1)
        trip.days.append(TripDay(local_date=date(2027, 4, 6)))
        s1.commit()
        trip_id = trip.id
    with session_factory() as s2:
        s2.add(TripDay(trip_id=trip_id, local_date=date(2027, 4, 6)))
        with pytest.raises(IntegrityError):
            s2.commit()
