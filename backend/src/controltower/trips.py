"""Trip rules that are computed, never stored (ARCHITECTURE.md: Trip, timeline rule)."""

from datetime import date, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from controltower.models import Item, ItemStatus, Trip


class TripPhase(StrEnum):
    UPCOMING = "upcoming"
    CURRENT = "current"
    PAST = "past"
    UNSCHEDULED = "unscheduled"  # no dates and no timed items yet


def local_date(moment: datetime, tz: str) -> date:
    return moment.astimezone(ZoneInfo(tz)).date()


def item_local_days(item: Item, home_tz: str) -> tuple[date, date] | None:
    """(start day, end day) in the item's own zones; None if it has no times."""
    start = item.effective_start
    if start is None:
        return None
    start_tz = item.start_tz or home_tz
    first = local_date(start, start_tz)
    end = item.effective_end
    last = local_date(end, item.end_tz or start_tz) if end else first
    return first, max(first, last)


def trip_date_range(trip: Trip) -> tuple[date | None, date | None]:
    """Stored dates win; any unset end is filled from the trip's timed items."""
    spans = [
        span
        for item in trip.items
        if item.status is not ItemStatus.CANCELLED
        and (span := item_local_days(item, trip.home_tz)) is not None
    ]
    first = trip.start_date or (min(s[0] for s in spans) if spans else None)
    last = trip.end_date or (max(s[1] for s in spans) if spans else None)
    return first, last


def trip_phase(trip: Trip, today: date | None = None) -> TripPhase:
    first, last = trip_date_range(trip)
    if first is None or last is None:
        return TripPhase.UNSCHEDULED
    today = today or datetime.now(ZoneInfo(trip.home_tz)).date()
    if today < first:
        return TripPhase.UPCOMING
    if today > last:
        return TripPhase.PAST
    return TripPhase.CURRENT
