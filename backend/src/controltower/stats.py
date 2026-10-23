"""Derived stats for a trip (ARCHITECTURE.md: Past trip record, "Derived stats").

Computed on every read, never stored (P6), so editing an item can't leave them stale.
A pure function over already-loaded objects, like build_timeline:

- Cancelled items are ignored everywhere.
- Cities and countries come from stays and activities only (plus the day extras' city),
  so the home airport of a flight doesn't count as a place you visited.
- Spend is summed per currency, no conversion. Skipped items count: you usually paid.
- Season is the meteorological season of the trip's middle date, flipped when most of
  those places with a latitude are in the southern hemisphere.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from controltower.models import ItemFeedback, ItemKind, ItemStatus, Place, Trip, Verdict
from controltower.trips import trip_date_range


class Season(StrEnum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"


_NORTH = {
    12: Season.WINTER, 1: Season.WINTER, 2: Season.WINTER,
    3: Season.SPRING, 4: Season.SPRING, 5: Season.SPRING,
    6: Season.SUMMER, 7: Season.SUMMER, 8: Season.SUMMER,
    9: Season.AUTUMN, 10: Season.AUTUMN, 11: Season.AUTUMN,
}  # fmt: skip
_FLIP = {
    Season.WINTER: Season.SUMMER,
    Season.SUMMER: Season.WINTER,
    Season.SPRING: Season.AUTUMN,
    Season.AUTUMN: Season.SPRING,
}

# Kinds that put you somewhere (not flights/transport) and kinds worth a 👍/👎.
VISITED_KINDS = {ItemKind.STAY, ItemKind.ACTIVITY}
RATEABLE_KINDS = {ItemKind.FLIGHT, ItemKind.STAY, ItemKind.TRANSPORT, ItemKind.ACTIVITY}
# Ideas never happened; skipped is its own signal (P4); cancelled is ignored.
UNRATEABLE_STATUSES = {ItemStatus.IDEA, ItemStatus.SKIPPED, ItemStatus.CANCELLED}


@dataclass
class FeedbackCounts:
    up: int = 0
    down: int = 0
    favourite: int = 0
    skipped: int = 0
    pending: int = 0  # rateable items with no feedback yet


@dataclass
class TripStats:
    nights: int | None
    cities: list[str]
    countries: list[str]
    flights: int
    spend: dict[str, Decimal]  # currency → total
    season: Season | None
    feedback: FeedbackCounts = field(default_factory=FeedbackCounts)


def season_of(day: date, southern: bool = False) -> Season:
    season = _NORTH[day.month]
    return _FLIP[season] if southern else season


def trip_stats(trip: Trip, feedback: Mapping[UUID, ItemFeedback]) -> TripStats:
    """Uses trip.items (with .place) and trip.days; `feedback` is mine, keyed by item id."""
    items = [i for i in trip.items if i.status is not ItemStatus.CANCELLED]
    first, last = trip_date_range(trip)

    visited: list[Place] = [i.place for i in items if i.kind in VISITED_KINDS and i.place]
    cities = {d.city for d in trip.days if d.city} | {p.city for p in visited if p.city}
    countries = {p.country for p in visited if p.country}

    spend: dict[str, Decimal] = {}
    for item in items:
        if item.cost_amount is not None and item.cost_currency:
            spend[item.cost_currency] = spend.get(item.cost_currency, Decimal(0)) + item.cost_amount

    season = None
    if first and last:
        lats = [p.lat for p in visited if p.lat is not None]
        southern = sum(lat < 0 for lat in lats) > len(lats) / 2
        season = season_of(first + timedelta(days=(last - first).days // 2), southern)

    counts = FeedbackCounts()
    for item in items:
        if item.status is ItemStatus.SKIPPED:
            counts.skipped += 1
        mine = feedback.get(item.id)
        if mine is None:
            if item.kind in RATEABLE_KINDS and item.status not in UNRATEABLE_STATUSES:
                counts.pending += 1
            continue
        counts.up += mine.verdict is Verdict.UP
        counts.down += mine.verdict is Verdict.DOWN
        counts.favourite += mine.favourite

    return TripStats(
        nights=(last - first).days if first and last else None,
        cities=sorted(cities),
        countries=sorted(countries),
        flights=sum(
            i.kind is ItemKind.FLIGHT and i.status is not ItemStatus.SKIPPED for i in items
        ),
        spend=dict(sorted(spend.items())),
        season=season,
        feedback=counts,
    )
