"""Request/response shapes for the HTTP API (Pydantic), separate from the ORM models.

Items are a discriminated union on `kind`: the same endpoint accepts a flight, stay,
transport, activity, or note, and the docs show each shape. Create bodies omit unset
fields so database defaults apply; PATCH bodies only change the fields they include.
"""

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Annotated, Any, ClassVar, Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)

from controltower.models import Item, ItemKind, ItemStatus, LogKind, LogSource, TransportMode
from controltower.timeline import Role
from controltower.trips import TripPhase


def _check_tz(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as err:
        raise ValueError(f"unknown time zone: {value!r} (use an IANA name)") from err
    return value


# Any offset is accepted ("2027-04-05T11:05:00-07:00"); naive times are rejected (422) and
# everything is converted to UTC, which is what the API returns.
UTCDatetime = Annotated[AwareDatetime, AfterValidator(lambda v: v.astimezone(UTC))]
TimeZone = Annotated[str, AfterValidator(_check_tz), Field(examples=["Asia/Tokyo"])]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$", examples=["USD"])]
Title = Annotated[str, Field(min_length=1, max_length=200)]


class Schema(BaseModel):
    """Inputs reject unknown fields, so a typo is a 422 instead of being ignored."""

    model_config = ConfigDict(extra="forbid")


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PatchSchema(Schema):
    """Fields listed in NOT_NULL may be omitted from a PATCH, but not sent as null."""

    NOT_NULL: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_null_for_required(self) -> Self:
        for name in self.NOT_NULL & self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


# --- Trips -----------------------------------------------------------------


class TripPatch(PatchSchema):
    NOT_NULL = frozenset({"title", "home_tz", "cancelled"})

    title: Title | None = None
    start_date: date | None = None
    end_date: date | None = None
    home_tz: TimeZone | None = None
    cancelled: bool | None = None
    notes: str | None = None


class TripCreate(Schema):
    title: Title
    start_date: date | None = None
    end_date: date | None = None
    home_tz: TimeZone
    notes: str | None = None


class TripRead(ReadSchema):
    id: UUID
    title: str
    start_date: date | None = Field(description="Stored start date, if set")
    end_date: date | None = Field(description="Stored end date, if set")
    first_day: date | None = Field(description="Effective first day (stored or from items)")
    last_day: date | None = Field(description="Effective last day (stored or from items)")
    phase: TripPhase
    home_tz: str
    cancelled: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


# --- Places ----------------------------------------------------------------


class PlacePatch(PatchSchema):
    NOT_NULL = frozenset({"name", "tz"})

    name: Title | None = None
    address: str | None = Field(None, max_length=400)
    city: str | None = Field(None, max_length=120)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$", examples=["JP"])
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    tz: TimeZone | None = None
    iata_code: str | None = Field(None, pattern=r"^[A-Z]{3}$", examples=["HND"])


class PlaceCreate(PlacePatch):
    name: Title
    tz: TimeZone


class PlaceRead(ReadSchema):
    id: UUID
    name: str
    address: str | None
    city: str | None
    country: str | None
    lat: float | None
    lon: float | None
    tz: str
    iata_code: str | None


# --- Items -----------------------------------------------------------------


class ItemFields(PatchSchema):
    """Fields every item kind shares. All optional here; creates tighten `title`."""

    NOT_NULL = frozenset({"title", "status"})

    title: Title | None = None
    status: ItemStatus | None = None
    planned_start: UTCDatetime | None = None
    planned_end: UTCDatetime | None = None
    actual_start: UTCDatetime | None = None
    actual_end: UTCDatetime | None = None
    start_tz: TimeZone | None = Field(None, description="Defaults to the place's, else the trip's")
    end_tz: TimeZone | None = Field(None, description="Defaults to to_place's, else start_tz")
    place_id: UUID | None = None
    to_place_id: UUID | None = None
    confirmation_code: str | None = Field(None, max_length=64)
    cost_amount: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=4)
    cost_currency: Currency | None = None
    notes: str | None = None


class FlightFields(BaseModel):
    airline: str | None = Field(None, max_length=3, examples=["UA"])
    flight_number: str | None = Field(None, max_length=8, examples=["837"])
    seat: str | None = Field(None, max_length=8)
    cabin: str | None = Field(None, max_length=32)
    terminal_from: str | None = Field(None, max_length=16)
    terminal_to: str | None = Field(None, max_length=16)
    gate: str | None = Field(None, max_length=16)
    aircraft: str | None = Field(None, max_length=64)
    booking_source: str | None = Field(None, max_length=64)


class StayFields(BaseModel):
    property_name: str | None = Field(None, max_length=200)
    room: str | None = Field(None, max_length=64)
    check_in_after: time | None = Field(None, examples=["15:00"])  # local wall-clock policy
    check_out_before: time | None = Field(None, examples=["11:00"])
    host_contact: str | None = Field(None, max_length=200)


class TransportFields(BaseModel):
    mode: TransportMode | None = None
    carrier: str | None = Field(None, max_length=120)
    vehicle_ref: str | None = Field(None, max_length=64)
    seat: str | None = Field(None, max_length=16)


class ActivityFields(BaseModel):
    category: str | None = Field(None, max_length=32, examples=["food"])
    booking_url: str | None = Field(None, max_length=1000)
    ticket_ref: str | None = Field(None, max_length=64)


class ItemCreateFields(ItemFields):
    title: Title
    status: ItemStatus = ItemStatus.PLANNED


class FlightCreate(ItemCreateFields, FlightFields):
    kind: Literal["flight"]


class StayCreate(ItemCreateFields, StayFields):
    kind: Literal["stay"]


class TransportCreate(ItemCreateFields, TransportFields):
    kind: Literal["transport"]


class ActivityCreate(ItemCreateFields, ActivityFields):
    kind: Literal["activity"]


class NoteCreate(ItemCreateFields):
    kind: Literal["note"]


ItemCreate = Annotated[
    FlightCreate | StayCreate | TransportCreate | ActivityCreate | NoteCreate,
    Field(discriminator="kind"),
]


class FlightPatch(ItemFields, FlightFields):
    kind: Literal["flight"]


class StayPatch(ItemFields, StayFields):
    kind: Literal["stay"]


class TransportPatch(ItemFields, TransportFields):
    NOT_NULL = ItemFields.NOT_NULL | {"mode"}
    kind: Literal["transport"]


class ActivityPatch(ItemFields, ActivityFields):
    kind: Literal["activity"]


class NotePatch(ItemFields):
    kind: Literal["note"]


ItemPatch = Annotated[
    FlightPatch | StayPatch | TransportPatch | ActivityPatch | NotePatch,
    Field(discriminator="kind"),
]


class ItemReadFields(ReadSchema):
    id: UUID
    trip_id: UUID
    title: str
    status: ItemStatus
    planned_start: datetime | None
    planned_end: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    effective_start: datetime | None = Field(description="actual_start, else planned_start")
    effective_end: datetime | None = Field(description="actual_end, else planned_end")
    start_tz: str | None
    end_tz: str | None
    place_id: UUID | None
    to_place_id: UUID | None
    confirmation_code: str | None
    cost_amount: Decimal | None
    cost_currency: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FlightRead(ItemReadFields, FlightFields):
    kind: Literal[ItemKind.FLIGHT]


class StayRead(ItemReadFields, StayFields):
    kind: Literal[ItemKind.STAY]


class TransportRead(ItemReadFields, TransportFields):
    kind: Literal[ItemKind.TRANSPORT]


class ActivityRead(ItemReadFields, ActivityFields):
    kind: Literal[ItemKind.ACTIVITY]


class NoteRead(ItemReadFields):
    kind: Literal[ItemKind.NOTE]


ItemRead = Annotated[
    FlightRead | StayRead | TransportRead | ActivityRead | NoteRead,
    Field(discriminator="kind"),
]

_ITEM_READ: TypeAdapter[ItemRead] = TypeAdapter(ItemRead)


def item_read(item: Item) -> ItemRead:
    """ORM item → the matching FlightRead/StayRead/... (chosen by `kind`)."""
    return _ITEM_READ.validate_python(item, from_attributes=True)


# --- Days and log ----------------------------------------------------------


class TripDayWrite(Schema):
    title: str | None = Field(None, max_length=200)
    city: str | None = Field(None, max_length=120)
    summary: str | None = None


class TripDayRead(ReadSchema):
    local_date: date
    title: str | None
    city: str | None
    summary: str | None


class LogEntryCreate(Schema):
    occurred_at: UTCDatetime
    tz: TimeZone
    source: LogSource = LogSource.MANUAL
    kind: LogKind
    text: str | None = None
    item_id: UUID | None = None
    place_id: UUID | None = None
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    raw: dict[str, Any] | None = None


class LogEntryRead(ReadSchema):
    id: UUID
    trip_id: UUID
    occurred_at: datetime
    tz: str
    source: LogSource
    kind: LogKind
    text: str | None
    item_id: UUID | None
    place_id: UUID | None
    lat: float | None
    lon: float | None
    raw: dict[str, Any] | None
    created_at: datetime


# --- Timeline (F2.3) -------------------------------------------------------


class ListingRead(BaseModel):
    role: Role = Field(description="single | starts | continues | ends, for this day")
    item: ItemRead


class DayRead(BaseModel):
    local_date: date
    number: int = Field(description="1-based day of the trip")
    title: str | None = Field(description="From the day's extras, if set")
    city: str | None
    summary: str | None
    items: list[ListingRead]
    log: list[LogEntryRead]


class TimelineRead(BaseModel):
    trip_id: UUID
    title: str
    home_tz: str
    first_day: date | None
    last_day: date | None
    phase: TripPhase
    days: list[DayRead]
    unscheduled: list[ItemRead] = Field(description="Items without times (e.g. ideas)")
