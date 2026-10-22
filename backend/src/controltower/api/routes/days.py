"""Per-day extras (title, city, summary). Days themselves are derived; see F2.3 timeline."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from controltower.api.deps import OwnerDep, SessionDep, get_trip, not_found
from controltower.api.schemas import TripDayRead, TripDayWrite
from controltower.models import TripDay

router = APIRouter(prefix="/trips/{trip_id}/days", tags=["days"])


@router.get("")
def list_days(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> list[TripDayRead]:
    """Only days that have extras set."""
    trip = get_trip(session, owner, trip_id)
    days = session.scalars(
        select(TripDay).where(TripDay.trip_id == trip.id).order_by(TripDay.local_date)
    )
    return [TripDayRead.model_validate(d) for d in days]


@router.put("/{local_date}")
def put_day(
    trip_id: UUID, local_date: date, body: TripDayWrite, session: SessionDep, owner: OwnerDep
) -> TripDayRead:
    """Create or replace a day's extras (fields left out are cleared)."""
    trip = get_trip(session, owner, trip_id)
    day = session.get(TripDay, (trip.id, local_date))
    if day is None:
        day = TripDay(trip=trip, local_date=local_date)
        session.add(day)
    for field, value in body.model_dump().items():
        setattr(day, field, value)
    session.commit()
    return TripDayRead.model_validate(day)


@router.delete("/{local_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day(trip_id: UUID, local_date: date, session: SessionDep, owner: OwnerDep) -> Response:
    trip = get_trip(session, owner, trip_id)
    day = session.get(TripDay, (trip.id, local_date))
    if day is None:
        raise not_found("day")
    session.delete(day)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
