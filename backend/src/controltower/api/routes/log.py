"""Trip log ("minutes"): timestamped observations. Manual for now; agents write here later."""

from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from controltower.api.deps import (
    OwnerDep,
    SessionDep,
    get_log_entry,
    get_trip,
    require_place,
    unprocessable,
)
from controltower.api.schemas import LogEntryCreate, LogEntryRead
from controltower.models import Item, LogEntry

router = APIRouter(tags=["log"])


@router.get("/trips/{trip_id}/log")
def list_log(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> list[LogEntryRead]:
    """Oldest first."""
    trip = get_trip(session, owner, trip_id)
    entries = session.scalars(
        select(LogEntry).where(LogEntry.trip_id == trip.id).order_by(LogEntry.occurred_at)
    )
    return [LogEntryRead.model_validate(e) for e in entries]


@router.post("/trips/{trip_id}/log", status_code=status.HTTP_201_CREATED)
def create_log_entry(
    trip_id: UUID, body: LogEntryCreate, session: SessionDep, owner: OwnerDep
) -> LogEntryRead:
    trip = get_trip(session, owner, trip_id)
    if body.item_id is not None:
        item = session.get(Item, body.item_id)
        if item is None or item.trip_id != trip.id:
            raise unprocessable(f"item_id: no item {body.item_id} on this trip")
    require_place(session, body.place_id, "place_id")
    entry = LogEntry(trip=trip, **body.model_dump(exclude_none=True))
    session.add(entry)
    session.commit()
    return LogEntryRead.model_validate(entry)


@router.delete("/log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log_entry(entry_id: UUID, session: SessionDep, owner: OwnerDep) -> Response:
    session.delete(get_log_entry(session, owner, entry_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
