"""Runtime settings, read from environment variables / the repo-root `.env`.

pydantic-settings validates types at startup, so a typo'd number fails fast instead of mid-poll.
Secrets are `SecretStr` so they never appear in logs or reprs.
"""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    opensky_client_id: str | None = None
    opensky_client_secret: SecretStr | None = None

    # Credits per day for the tier (anonymous 400, free account 4000, feeder 8000).
    opensky_daily_credits: int = Field(default=4000, gt=0)
    # Fraction of the daily budget held back for on-demand calls (tracks, retries).
    credit_reserve_fraction: float = Field(default=0.1, ge=0, lt=1)

    # Area polled each cycle as "lat_min,lon_min,lat_max,lon_max"; empty = global.
    poll_bbox: str = ""
    # Stop polling when no API request has arrived for this long (saves credits overnight).
    idle_pause_s: int = Field(default=600, gt=0)

    # Aircraft not heard from for longer than this are dropped from responses.
    stale_after_s: int = Field(default=60, gt=0)
    # How much path history we accumulate per aircraft from our own polls.
    track_history_s: int = Field(default=2 * 3600, gt=0)
    route_cache_ttl_s: int = Field(default=24 * 3600, gt=0)
