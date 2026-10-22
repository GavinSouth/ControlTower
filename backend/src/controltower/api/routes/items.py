"""Items: the per-kind itinerary entries of a trip.

One endpoint for every kind: the body's `kind` picks the shape (and the ORM subclass).
After every create/update the same rules run: places must exist, missing zones are
filled in (place → trip home zone), and ends may not precede starts.
"""

from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectin_polymorphic

from controltower.api.deps import (
    OwnerDep,
    SessionDep,
    get_item,
    get_trip,
    require_place,
    unprocessable,
)
from controltower.api.schemas import ItemCreate, ItemPatch, ItemRead, item_read
from controltower.models import Activity, Flight, Item, ItemKind, Note, Stay, Transport, Trip

router = APIRouter(tags=["items"])

ORM_BY_KIND: dict[str, type[Item]] = {
    ItemKind.FLIGHT: Flight,
    ItemKind.STAY: Stay,
    ItemKind.TRANSPORT: Transport,
    ItemKind.ACTIVITY: Activity,
    ItemKind.NOTE: Note,
}

# Load every kind's detail columns up front (one extra query per kind present),
# instead of one lazy query per item when the response is built.
DETAIL_KINDS = [Flight, Stay, Transport, Activity]


def apply_item_rules(session: Session, item: Item, trip: Trip) -> None:
    # Look up places without flushing the (possibly invalid) item first; a bad id must
    # become a 422 here, not a foreign-key error from the database.
    with session.no_autoflush:
        place = require_place(session, item.place_id, "place_id")
        to_place = require_place(session, item.to_place_id, "to_place_id")

    # A timed item must be placeable on a local day, so it always gets a zone.
    if item.start_tz is None and (place or item.effective_start):
        item.start_tz = place.tz if place else trip.home_tz
    if item.end_tz is None and to_place:
        item.end_tz = to_place.tz

    for label, start, end in (
        ("planned", item.planned_start, item.planned_end),
        ("actual", item.actual_start, item.actual_end),
    ):
        if start and end and end < start:
            raise unprocessable(f"{label}_end is before {label}_start")


@router.get("/trips/{trip_id}/items")
def list_items(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> list[ItemRead]:
    """A trip's items in time order (actual time if recorded); untimed items last."""
    trip = get_trip(session, owner, trip_id)
    when = func.coalesce(Item.actual_start, Item.planned_start)
    items = session.scalars(
        select(Item)
        .where(Item.trip_id == trip.id)
        .options(selectin_polymorphic(Item, DETAIL_KINDS))
        .order_by(when.asc().nulls_last(), Item.title)
    ).all()
    return [item_read(i) for i in items]


@router.post("/trips/{trip_id}/items", status_code=status.HTTP_201_CREATED)
def create_item(trip_id: UUID, body: ItemCreate, session: SessionDep, owner: OwnerDep) -> ItemRead:
    trip = get_trip(session, owner, trip_id)
    item = ORM_BY_KIND[body.kind](trip=trip, **body.model_dump(exclude_none=True, exclude={"kind"}))
    session.add(item)
    apply_item_rules(session, item, trip)
    session.commit()
    return item_read(item)


@router.get("/items/{item_id}")
def read_item(item_id: UUID, session: SessionDep, owner: OwnerDep) -> ItemRead:
    return item_read(get_item(session, owner, item_id))


@router.patch("/items/{item_id}")
def update_item(item_id: UUID, body: ItemPatch, session: SessionDep, owner: OwnerDep) -> ItemRead:
    """Send `kind` plus only the fields to change; send null to clear an optional field."""
    item = get_item(session, owner, item_id)
    if body.kind != item.kind:
        raise unprocessable(f"kind is {item.kind!s}; an item's kind can't change")
    for field, value in body.model_dump(exclude_unset=True, exclude={"kind"}).items():
        setattr(item, field, value)
    apply_item_rules(session, item, item.trip)
    session.commit()
    return item_read(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: UUID, session: SessionDep, owner: OwnerDep) -> Response:
    """Log entries that referenced the item are kept; their link is cleared."""
    session.delete(get_item(session, owner, item_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
