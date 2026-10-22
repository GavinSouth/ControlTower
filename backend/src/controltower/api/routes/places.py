"""Places: reusable locations (airports, hotels, sights) shared across trips."""

from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import or_, select

from controltower.api.deps import SessionDep, get_place
from controltower.api.schemas import PlaceCreate, PlacePatch, PlaceRead
from controltower.models import Place

router = APIRouter(prefix="/places", tags=["places"])


@router.get("")
def search_places(session: SessionDep, q: str | None = None, limit: int = 50) -> list[PlaceRead]:
    """Match `q` against name, city, or IATA code (case-insensitive)."""
    query = select(Place).order_by(Place.name).limit(min(limit, 200))
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(Place.name.ilike(pattern), Place.city.ilike(pattern), Place.iata_code.ilike(q))
        )
    return [PlaceRead.model_validate(p) for p in session.scalars(query)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_place(body: PlaceCreate, session: SessionDep) -> PlaceRead:
    place = Place(**body.model_dump(exclude_none=True))
    session.add(place)
    session.commit()
    return PlaceRead.model_validate(place)


@router.get("/{place_id}")
def read_place(place_id: UUID, session: SessionDep) -> PlaceRead:
    return PlaceRead.model_validate(get_place(session, place_id))


@router.patch("/{place_id}")
def update_place(place_id: UUID, body: PlacePatch, session: SessionDep) -> PlaceRead:
    place = get_place(session, place_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(place, field, value)
    session.commit()
    return PlaceRead.model_validate(place)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place(place_id: UUID, session: SessionDep) -> Response:
    """Items and log entries that used the place keep existing, without it."""
    session.delete(get_place(session, place_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
