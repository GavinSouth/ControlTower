"""The demo trips are valid, exercise the timeline and stats, and are only created once."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from controltower.demo import create_demo_trip, create_past_demo_trip
from controltower.models import ItemFeedback, TripReflection
from controltower.stats import trip_stats
from controltower.timeline import Role, build_timeline
from controltower.trips import TripPhase, trip_phase


def test_demo_trip_builds_a_timeline_and_is_idempotent(session: Session) -> None:
    trip = create_demo_trip(session)
    assert trip is not None
    timeline = build_timeline(trip)
    assert [d.number for d in timeline.days] == [1, 2, 3, 4, 5]  # 5 Apr (SFO) .. 9 Apr
    roles = {(li.item.title, li.role) for d in timeline.days for li in d.listings}
    assert ("SFO → HND", Role.STARTS) in roles and ("Hotel Gracery", Role.CONTINUES) in roles
    assert [i.title for i in timeline.unscheduled] == ["Maybe: teamLab Planets"]
    assert create_demo_trip(session) is None


def test_past_demo_trip_is_past_half_rated_and_idempotent(session: Session) -> None:
    trip = create_past_demo_trip(session)
    assert trip is not None
    assert trip_phase(trip) is TripPhase.PAST
    feedback = {
        f.item_id: f
        for f in session.scalars(
            select(ItemFeedback).where(ItemFeedback.item_id.in_([i.id for i in trip.items]))
        )
    }
    stats = trip_stats(trip, feedback)
    assert (stats.nights, stats.cities, stats.countries) == (5, ["Lisbon", "Sintra"], ["PT"])
    assert (stats.feedback.favourite, stats.feedback.skipped) == (2, 1)
    assert stats.feedback.pending > 0  # leaves something to rate in the app
    assert session.get(TripReflection, (trip.id, trip.owner_id)) is None  # not reflected yet
    assert create_past_demo_trip(session) is None
