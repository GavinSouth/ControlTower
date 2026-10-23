"""Derived trip stats (pure function, no database)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from controltower.models import (
    Activity,
    Flight,
    Item,
    ItemFeedback,
    ItemStatus,
    Note,
    Place,
    Stay,
    Trip,
    TripDay,
    Verdict,
)
from controltower.stats import Season, season_of, trip_stats

LISBON_TZ = ZoneInfo("Europe/Lisbon")
LISBON = Place(name="Hotel", city="Lisbon", country="PT", lat=38.7, tz="Europe/Lisbon")
SINTRA = Place(name="Pena Palace", city="Sintra", country="PT", lat=38.8, tz="Europe/Lisbon")
SFO = Place(name="SFO", city="San Francisco", country="US", lat=37.6, tz="America/Los_Angeles")


def at(day: int, hour: int = 12) -> datetime:
    return datetime(2025, 5, day, hour, tzinfo=LISBON_TZ)


def trip_of(*items: Item, **fields: object) -> Trip:
    return Trip(title="Lisbon", home_tz="Europe/Lisbon", items=list(items), **fields)


def activity(title: str, day: int, **fields: object) -> Activity:
    return Activity(
        id=uuid.uuid4(), title=title, planned_start=at(day), start_tz="Europe/Lisbon", **fields
    )


def test_nights_cities_countries_and_flights() -> None:
    trip = trip_of(
        Flight(id=uuid.uuid4(), title="SFO→LIS", planned_start=at(10, 8), place=SFO),
        Stay(
            id=uuid.uuid4(), title="Hotel", planned_start=at(10), planned_end=at(15), place=LISBON
        ),
        activity("Pena Palace", 12, place=SINTRA),
        activity("Tram ride", 13),
        Flight(id=uuid.uuid4(), title="Skipped", planned_start=at(14), status=ItemStatus.SKIPPED),
    )
    trip.days = [TripDay(local_date=date(2025, 5, 11), city="Cascais")]

    stats = trip_stats(trip, {})

    assert stats.nights == 5
    # The flight's SFO doesn't count as visited; the day extras' city does.
    assert stats.cities == ["Cascais", "Lisbon", "Sintra"]
    assert stats.countries == ["PT"]
    assert stats.flights == 1  # the skipped flight doesn't count


def test_spend_is_per_currency_and_skips_cancelled_items() -> None:
    trip = trip_of(
        activity("Dinner", 10, cost_amount=Decimal("40.50"), cost_currency="EUR"),
        activity("Tram", 11, cost_amount=Decimal("3"), cost_currency="EUR"),
        activity("Tour", 12, cost_amount=Decimal("100"), cost_currency="USD"),
        activity(
            "Paid, skipped",
            12,
            cost_amount=Decimal("10"),
            cost_currency="EUR",
            status=ItemStatus.SKIPPED,
        ),
        activity(
            "Refunded",
            13,
            cost_amount=Decimal("999"),
            cost_currency="EUR",
            status=ItemStatus.CANCELLED,
        ),
    )
    assert trip_stats(trip, {}).spend == {"EUR": Decimal("53.50"), "USD": Decimal("100")}


def test_season_uses_the_middle_date_and_flips_south() -> None:
    assert season_of(date(2025, 5, 12)) is Season.SPRING
    assert season_of(date(2025, 12, 1)) is Season.WINTER
    assert season_of(date(2025, 12, 1), southern=True) is Season.SUMMER

    # Feb 25 → Mar 10: the middle (Mar 4) is spring, though it starts in winter.
    north = trip_of(start_date=date(2025, 2, 25), end_date=date(2025, 3, 10))
    assert trip_stats(north, {}).season is Season.SPRING

    sydney = Place(name="Hotel", city="Sydney", country="AU", lat=-33.9, tz="Australia/Sydney")
    south = trip_of(
        Stay(id=uuid.uuid4(), title="Hotel", place=sydney),
        start_date=date(2025, 1, 5),
        end_date=date(2025, 1, 9),
    )
    assert trip_stats(south, {}).season is Season.SUMMER

    assert trip_stats(trip_of(), {}).season is None  # no dates at all


def test_feedback_counts_and_pending() -> None:
    liked, disliked, unrated = activity("A", 10), activity("B", 11), activity("C", 12)
    skipped = activity("D", 12, status=ItemStatus.SKIPPED)
    idea = activity("E", 13, status=ItemStatus.IDEA)
    note = Note(id=uuid.uuid4(), title="Note", planned_start=at(13))
    trip = trip_of(liked, disliked, unrated, skipped, idea, note)
    feedback = {
        liked.id: ItemFeedback(verdict=Verdict.UP, favourite=True),
        disliked.id: ItemFeedback(verdict=Verdict.DOWN, favourite=False),
    }

    counts = trip_stats(trip, feedback).feedback

    assert (counts.up, counts.down, counts.favourite, counts.skipped) == (1, 1, 1, 1)
    assert counts.pending == 1  # only C: skipped, ideas and notes aren't asked for
