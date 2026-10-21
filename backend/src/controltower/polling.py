"""Polling strategy: how often we can afford to call the state provider.

One backend poller fetches a snapshot and every user reads the cached copy, so cost scales with
time, not users. The interval is the slower of (a) the provider's data resolution and (b) what
the daily credit budget allows. Example, free account, global box (4 credits):
4000 * 0.9 / 4 = 900 polls/day -> one every 96 s.
"""

import math

SECONDS_PER_DAY = 86_400


def poll_interval_s(
    *,
    daily_credits: int,
    cost_per_poll: int,
    min_refresh_s: int,
    reserve_fraction: float = 0.1,
) -> int:
    """Seconds between polls that keep 24/7 polling within budget."""
    usable = daily_credits * (1 - reserve_fraction)
    polls_per_day = usable / cost_per_poll
    if polls_per_day < 1:
        raise ValueError("budget cannot afford one poll per day")
    return max(min_refresh_s, math.ceil(SECONDS_PER_DAY / polls_per_day))


class Poller:
    """Background task (FastAPI lifespan) that keeps the store fresh.

    Phase 2 loop:
      1. if no API request within `idle_pause_s` -> sleep, skip the call (demand-driven).
      2. fetch_states(bbox); on success -> store.put_snapshot(); record credits_remaining.
      3. on RateLimitedError -> sleep retry_after_s; on ProviderError -> exponential backoff,
         keep serving the last snapshot (responses expose its age so clients can show "stale").
      4. if credits_remaining is below the reserve -> stretch the interval for the rest of day.
      5. new callsigns -> queue route lookups (rate-limited, cached incl. misses).
    """

    async def run(self) -> None:
        raise NotImplementedError("Phase 2")
