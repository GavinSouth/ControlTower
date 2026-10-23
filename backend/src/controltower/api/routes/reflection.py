"""Past trip record (F3.4): my reflection on a trip, my feedback on items, stats, favourites.

Opinions are always "mine" (the owner's), keyed by user, so shared trips later (Phase 6)
only change who "me" is. See ARCHITECTURE.md: Past trip record.
"""

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectin_polymorphic, selectinload

from controltower.api.deps import OwnerDep, SessionDep, get_item, get_trip, not_found
from controltower.api.routes.items import DETAIL_KINDS
from controltower.api.schemas import (
    FavouriteRead,
    ItemFeedbackRead,
    ItemFeedbackWrite,
    PlaceRead,
    ReflectionRead,
    ReflectionWrite,
    TripStatsRead,
    item_read,
)
from controltower.models import Activity, Item, ItemFeedback, ItemKind, Trip, TripReflection, User
from controltower.stats import trip_stats

router = APIRouter(tags=["past trips"])

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def my_reflections(
    session: Session, owner: User, trip_ids: Iterable[UUID]
) -> dict[UUID, TripReflection]:
    """My reflections on these trips, by trip id (one query for the whole trip list)."""
    rows = session.scalars(
        select(TripReflection).where(
            TripReflection.user_id == owner.id, TripReflection.trip_id.in_(list(trip_ids))
        )
    )
    return {r.trip_id: r for r in rows}


def my_feedback(
    session: Session, owner: User, item_ids: Iterable[UUID]
) -> dict[UUID, ItemFeedback]:
    rows = session.scalars(
        select(ItemFeedback).where(
            ItemFeedback.user_id == owner.id, ItemFeedback.item_id.in_(list(item_ids))
        )
    )
    return {f.item_id: f for f in rows}


# --- Reflection --------------------------------------------------------------


@router.get("/trips/{trip_id}/reflection")
def read_reflection(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> ReflectionRead:
    """404 until I've reflected on the trip."""
    trip = get_trip(session, owner, trip_id)
    reflection = session.get(TripReflection, (trip.id, owner.id))
    if reflection is None:
        raise not_found("reflection")
    return ReflectionRead.model_validate(reflection)


@router.put("/trips/{trip_id}/reflection")
def put_reflection(
    trip_id: UUID, body: ReflectionWrite, session: SessionDep, owner: OwnerDep
) -> ReflectionRead:
    """Create or replace my reflection: fields left out are cleared."""
    trip = get_trip(session, owner, trip_id)
    reflection = session.get(TripReflection, (trip.id, owner.id))
    if reflection is None:
        reflection = TripReflection(trip_id=trip.id, user_id=owner.id)
        session.add(reflection)
    for field, value in body.model_dump().items():
        setattr(reflection, field, value)
    session.commit()
    return ReflectionRead.model_validate(reflection)


@router.delete("/trips/{trip_id}/reflection", status_code=status.HTTP_204_NO_CONTENT)
def delete_reflection(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> Response:
    """Idempotent: deleting a reflection that doesn't exist is fine."""
    trip = get_trip(session, owner, trip_id)
    reflection = session.get(TripReflection, (trip.id, owner.id))
    if reflection is not None:
        session.delete(reflection)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Item feedback -----------------------------------------------------------


@router.put("/items/{item_id}/feedback")
def put_feedback(
    item_id: UUID, body: ItemFeedbackWrite, session: SessionDep, owner: OwnerDep
) -> ItemFeedbackRead | None:
    """Replace my 👍/👎, ♥ and review. Returns null when that leaves nothing to keep."""
    item = get_item(session, owner, item_id)
    feedback = session.get(ItemFeedback, (item.id, owner.id))
    if feedback is None:
        feedback = ItemFeedback(item_id=item.id, user_id=owner.id)
        session.add(feedback)
    for field, value in body.model_dump().items():
        setattr(feedback, field, value)
    if feedback.is_empty:
        # A pending (new) row is just dropped; a stored one is deleted.
        session.expunge(feedback) if feedback in session.new else session.delete(feedback)
        session.commit()
        return None
    session.commit()
    return ItemFeedbackRead.model_validate(feedback)


@router.delete("/items/{item_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(item_id: UUID, session: SessionDep, owner: OwnerDep) -> Response:
    item = get_item(session, owner, item_id)
    feedback = session.get(ItemFeedback, (item.id, owner.id))
    if feedback is not None:
        session.delete(feedback)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Stats and favourites ----------------------------------------------------


@router.get("/trips/{trip_id}/stats")
def read_stats(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> TripStatsRead:
    """Derived on every read: nights, cities, countries, flights, spend, season, feedback."""
    trip = session.scalars(
        select(Trip)
        .where(Trip.id == trip_id, Trip.owner_id == owner.id)
        .options(selectinload(Trip.items).selectinload(Item.place), selectinload(Trip.days))
    ).one_or_none()
    if trip is None:
        raise not_found("trip")
    stats = trip_stats(trip, my_feedback(session, owner, (i.id for i in trip.items)))
    return TripStatsRead.model_validate(stats)


@router.get("/favourites")
def list_favourites(
    session: SessionDep,
    owner: OwnerDep,
    country: str | None = None,
    kind: ItemKind | None = None,
    category: str | None = None,
) -> list[FavouriteRead]:
    """Items I ♥'d across all trips, most recent first (untimed last).

    Filters: the place's country ("JP"), item kind, activity category ("food").
    """
    rows = session.execute(
        select(ItemFeedback, Item)
        .join(Item, Item.id == ItemFeedback.item_id)
        .join(Trip, Trip.id == Item.trip_id)
        .where(ItemFeedback.user_id == owner.id, ItemFeedback.favourite, Trip.owner_id == owner.id)
        .options(
            selectin_polymorphic(Item, DETAIL_KINDS),
            selectinload(Item.place),
            selectinload(Item.trip),
        )
    ).all()
    out = []
    for feedback, item in rows:
        if kind is not None and item.kind is not kind:
            continue
        if category is not None and (not isinstance(item, Activity) or item.category != category):
            continue
        if country is not None and (item.place is None or item.place.country != country.upper()):
            continue
        out.append(
            FavouriteRead(
                trip_id=item.trip_id,
                trip_title=item.trip.title,
                item=item_read(item, feedback),
                place=PlaceRead.model_validate(item.place) if item.place else None,
            )
        )
    return sorted(out, key=lambda f: f.item.effective_start or _EPOCH, reverse=True)
