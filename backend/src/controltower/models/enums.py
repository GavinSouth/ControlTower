"""Enumerations stored as strings (see types.str_enum). Values are the stored text."""

from enum import StrEnum


class ItemKind(StrEnum):
    FLIGHT = "flight"
    STAY = "stay"
    TRANSPORT = "transport"
    ACTIVITY = "activity"
    NOTE = "note"


class ItemStatus(StrEnum):
    IDEA = "idea"  # wishlist; may have no times and then sits outside the day timeline
    PLANNED = "planned"
    BOOKED = "booked"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TransportMode(StrEnum):
    TRAIN = "train"
    METRO = "metro"
    BUS = "bus"
    CAR = "car"
    RIDESHARE = "rideshare"
    TAXI = "taxi"
    FERRY = "ferry"
    BIKE = "bike"
    WALK = "walk"
    OTHER = "other"


class LogSource(StrEnum):
    MANUAL = "manual"
    AGENT = "agent"
    LOCATION = "location"
    CALENDAR = "calendar"
    EMAIL = "email"
    PHOTO = "photo"


class LogKind(StrEnum):
    CHECK_IN = "check_in"
    ARRIVAL = "arrival"
    DEPARTURE = "departure"
    NOTE = "note"
    SUMMARY = "summary"


class Verdict(StrEnum):
    UP = "up"
    DOWN = "down"
