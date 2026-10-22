"""The day-by-day view of a trip (built by controltower.timeline.build_timeline)."""

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from controltower.api.deps import OwnerDep, SessionDep, not_found, unprocessable
from controltower.api.routes.items import DETAIL_KINDS
from controltower.api.schemas import (
    DayRead,
    ListingRead,
    LogEntryRead,
    TimelineRead,
    item_read,
)
from controltower.models import Trip
from controltower.timeline import TimelineTooLongError, build_timeline

router = APIRouter(tags=["timeline"])


@router.get("/trips/{trip_id}/timeline")
def read_timeline(trip_id: UUID, session: SessionDep, owner: OwnerDep) -> TimelineRead:
    """Every local day of the trip with its items (and their role that day) and log."""
    trip = session.scalars(
        select(Trip)
        .where(Trip.id == trip_id, Trip.owner_id == owner.id)
        .options(
            # A fixed number of queries however many items: items + one per detail
            # kind, log entries, and day extras.
            selectinload(Trip.items).selectin_polymorphic(DETAIL_KINDS),
            selectinload(Trip.log_entries),
            selectinload(Trip.days),
        )
    ).one_or_none()
    if trip is None:
        raise not_found("trip")
    try:
        timeline = build_timeline(trip)
    except TimelineTooLongError as err:
        raise unprocessable(str(err)) from err

    return TimelineRead(
        trip_id=trip.id,
        title=trip.title,
        home_tz=trip.home_tz,
        first_day=timeline.first_day,
        last_day=timeline.last_day,
        phase=timeline.phase,
        days=[
            DayRead(
                local_date=day.local_date,
                number=day.number,
                title=day.extras.title if day.extras else None,
                city=day.extras.city if day.extras else None,
                summary=day.extras.summary if day.extras else None,
                items=[ListingRead(role=li.role, item=item_read(li.item)) for li in day.listings],
                log=[LogEntryRead.model_validate(e) for e in day.log],
            )
            for day in timeline.days
        ],
        unscheduled=[item_read(i) for i in timeline.unscheduled],
    )
