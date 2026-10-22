"""The day-by-day timeline (ARCHITECTURE.md: "How days are derived").

A pure function over already-loaded objects, so it's testable without a database:

- The days run from the trip's first to last day (stored dates, else timed items),
  widened to include any log entries and day extras. Every date is a day, even empty ones.
- An item is listed on each local date from its start day (in `start_tz`) to its end
  day (in `end_tz`) that falls inside the range, tagged with a role. Items without times
  go to `unscheduled`. Cancelled items are listed but never widen the range.
- Within a day, `continues` listings come first, then the rest by the time that
  matters that day (start for starts/single, end for ends).
- Log entries land on the local date of `occurred_at` in their own zone.
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

from controltower.models import Item, LogEntry, Trip, TripDay
from controltower.trips import TripPhase, item_local_days, local_date, trip_date_range, trip_phase

MAX_DAYS = 366


class Role(StrEnum):
    SINGLE = "single"  # starts and ends this day
    STARTS = "starts"
    CONTINUES = "continues"  # e.g. night 2 of a stay
    ENDS = "ends"


@dataclass(frozen=True)
class Listing:
    item: Item
    role: Role


@dataclass
class Day:
    local_date: date
    number: int  # 1-based "Day 3"
    extras: TripDay | None = None
    listings: list[Listing] = field(default_factory=list)
    log: list[LogEntry] = field(default_factory=list)


@dataclass
class Timeline:
    first_day: date | None
    last_day: date | None
    phase: TripPhase
    days: list[Day]
    unscheduled: list[Item]


class TimelineTooLongError(ValueError):
    pass


def role_on(day: date, first: date, last: date) -> Role:
    if first == last:
        return Role.SINGLE
    if day == first:
        return Role.STARTS
    if day == last:
        return Role.ENDS
    return Role.CONTINUES


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _sort_key(listing: Listing) -> tuple[int, datetime, str]:
    item = listing.item
    if listing.role is Role.CONTINUES:
        return (0, item.effective_start or _EPOCH, item.title)
    moment = item.effective_end if listing.role is Role.ENDS else item.effective_start
    return (1, moment or _EPOCH, item.title)


def build_timeline(trip: Trip, today: date | None = None) -> Timeline:
    """Uses trip.items, trip.log_entries, and trip.days (load them eagerly for speed)."""
    items, log_entries, day_extras = trip.items, trip.log_entries, trip.days
    spans = {id(i): span for i in items if (span := item_local_days(i, trip.home_tz))}
    unscheduled = sorted((i for i in items if id(i) not in spans), key=lambda i: i.title)
    log_days = [(e, local_date(e.occurred_at, e.tz)) for e in log_entries]

    first, last = trip_date_range(trip)
    extra_dates = [d for _, d in log_days] + [x.local_date for x in day_extras]
    if extra_dates:
        first = min([first, *extra_dates] if first else extra_dates)
        last = max([last, *extra_dates] if last else extra_dates)
    phase = trip_phase(trip, today)
    if first is None or last is None:
        return Timeline(None, None, phase, [], unscheduled)

    count = (last - first).days + 1
    if count > MAX_DAYS:
        raise TimelineTooLongError(
            f"timeline spans {count} days ({first} to {last}); the maximum is {MAX_DAYS}"
        )

    extras = {x.local_date: x for x in day_extras}
    days = [
        Day(local_date=d, number=n + 1, extras=extras.get(d))
        for n, d in enumerate(first + timedelta(days=k) for k in range(count))
    ]
    by_date = {d.local_date: d for d in days}

    for item in items:
        if (span := spans.get(id(item))) is None:
            continue
        start_day, end_day = span
        for k in range((min(end_day, last) - max(start_day, first)).days + 1):
            day = max(start_day, first) + timedelta(days=k)
            by_date[day].listings.append(Listing(item, role_on(day, start_day, end_day)))

    for entry, day in log_days:
        by_date[day].log.append(entry)

    for d in days:
        d.listings.sort(key=_sort_key)
        d.log.sort(key=lambda e: e.occurred_at)
    return Timeline(first, last, phase, days, unscheduled)
