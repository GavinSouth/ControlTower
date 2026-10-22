"""The demo trip is valid, exercises the timeline, and is only created once."""

from sqlalchemy.orm import Session

from controltower.demo import create_demo_trip
from controltower.timeline import Role, build_timeline


def test_demo_trip_builds_a_timeline_and_is_idempotent(session: Session) -> None:
    trip = create_demo_trip(session)
    assert trip is not None
    timeline = build_timeline(trip)
    assert [d.number for d in timeline.days] == [1, 2, 3, 4, 5]  # 5 Apr (SFO) .. 9 Apr
    roles = {(li.item.title, li.role) for d in timeline.days for li in d.listings}
    assert ("SFO → HND", Role.STARTS) in roles and ("Hotel Gracery", Role.CONTINUES) in roles
    assert [i.title for i in timeline.unscheduled] == ["Maybe: teamLab Planets"]
    assert create_demo_trip(session) is None
