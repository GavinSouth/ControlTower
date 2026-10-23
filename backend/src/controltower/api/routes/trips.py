"""Trips: list (filter by phase), create, read, update, delete."""

from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from controltower.api.deps import OwnerDep, PhotoStoreDep, SessionDep, get_trip, unprocessable
from controltower.api.routes.reflection import my_reflections
from controltower.api.schemas import TripCreate, TripPatch, TripRead
from controltower.models import Trip, TripReflection, User
from controltower.trips import TripPhase, trip_date_range, trip_phase

router = APIRouter(prefix="/trips", tags=["trips"])


def trip_read(trip: Trip, reflection: TripReflection | None) -> TripRead:
    first, last = trip_date_range(trip)
    return TripRead.model_validate(
        {
            **{f: getattr(trip, f) for f in TripRead.model_fields if hasattr(trip, f)},
            "first_day": first,
            "last_day": last,
            "phase": trip_phase(trip),
            "reflection": reflection,
            "cover": trip.cover_photo,
        }
    )


def check_dates(trip: Trip) -> None:
    if trip.start_date and trip.end_date and trip.end_date < trip.start_date:
        raise unprocessable("end_date is before start_date")


@router.get("")
def list_trips(
    session: SessionDep, owner: OwnerDep, phase: TripPhase | None = None
) -> list[TripRead]:
    """All trips, soonest first; undated trips last. Optionally filter by phase."""
    trips = session.scalars(
        select(Trip)
        .where(Trip.owner_id == owner.id)
        .options(selectinload(Trip.items), selectinload(Trip.cover_photo))
    ).all()
    reflections = my_reflections(session, owner, (t.id for t in trips))
    out = [trip_read(t, reflections.get(t.id)) for t in trips]
    if phase is not None:
        out = [t for t in out if t.phase is phase]
    return sorted(out, key=lambda t: (t.first_day is None, t.first_day, t.title))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_trip(body: TripCreate, session: SessionDep, owner: OwnerDep) -> TripRead:
    trip = Trip(owner=owner, **body.model_dump())
    check_dates(trip)
    session.add(trip)
    session.commit()
    return trip_read(trip, reflection=None)


def my_trip_read(session: Session, owner: User, trip: Trip) -> TripRead:
    return trip_read(trip, my_reflections(session, owner, [trip.id]).get(trip.id))


@router.get("/{trip_id}")
def read_trip(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> TripRead:
    return my_trip_read(session, owner, get_trip(session, owner, trip_id))


@router.patch("/{trip_id}")
def update_trip(trip_id: UUID, body: TripPatch, session: SessionDep, owner: OwnerDep) -> TripRead:
    trip = get_trip(session, owner, trip_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    check_dates(trip)
    session.commit()
    return my_trip_read(session, owner, trip)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: UUID, session: SessionDep, owner: OwnerDep, store: PhotoStoreDep
) -> Response:
    """Deletes the trip with its items, days, log entries, and cover photo. Places are kept."""
    trip = get_trip(session, owner, trip_id)
    cover = trip.cover_photo
    session.delete(trip)
    if cover is not None:
        session.delete(cover)
    session.commit()
    if cover is not None:
        store.delete(cover.id)  # files only after the commit, so a failed delete keeps them
    return Response(status_code=status.HTTP_204_NO_CONTENT)
