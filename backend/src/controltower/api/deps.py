"""Request dependencies: a database session per request, the owner, and 404 lookups.

Every lookup is scoped to the owner, so adding accounts later (Phase 6) only changes how
the owner is found, not the routes.
"""

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from controltower.db import get_or_create_owner
from controltower.models import Item, LogEntry, Place, Trip, User
from controltower.photos import PhotoStore


def get_session(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_owner(session: SessionDep) -> User:
    owner = get_or_create_owner(session)
    session.commit()  # persist "me" on first use, even for read-only requests
    return owner


OwnerDep = Annotated[User, Depends(get_owner)]


def get_photo_store(request: Request) -> PhotoStore:
    store: PhotoStore = request.app.state.photo_store
    return store


PhotoStoreDep = Annotated[PhotoStore, Depends(get_photo_store)]


def not_found(what: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"{what} not found")


def unprocessable(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


def get_trip(session: Session, owner: User, trip_id: UUID) -> Trip:
    trip = session.get(Trip, trip_id)
    if trip is None or trip.owner_id != owner.id:
        raise not_found("trip")
    return trip


def get_item(session: Session, owner: User, item_id: UUID) -> Item:
    item = session.get(Item, item_id)
    if item is None or item.trip.owner_id != owner.id:
        raise not_found("item")
    return item


def get_log_entry(session: Session, owner: User, entry_id: UUID) -> LogEntry:
    entry = session.get(LogEntry, entry_id)
    if entry is None or entry.trip.owner_id != owner.id:
        raise not_found("log entry")
    return entry


def get_place(session: Session, place_id: UUID) -> Place:
    place = session.get(Place, place_id)
    if place is None:
        raise not_found("place")
    return place


def require_place(session: Session, place_id: UUID | None, field: str) -> Place | None:
    """Resolve a place id from a request body; an unknown id is a 422, not a 404."""
    if place_id is None:
        return None
    place = session.get(Place, place_id)
    if place is None:
        raise unprocessable(f"{field}: no place with id {place_id}")
    return place
