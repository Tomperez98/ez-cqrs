"""date utils."""
from __future__ import annotations

import datetime


def now() -> datetime.datetime:
    """Currrent time in the system."""
    return datetime.datetime.now(
        tz=datetime.timezone.utc,
    ).replace(microsecond=0)


def to_unix(dt: datetime.datetime) -> float:
    """Convert datetime to unix timestamp."""
    return int(dt.replace(microsecond=0).timestamp())


def from_unix(dt: int) -> datetime.datetime:
    """Convert unix timestamp to datetime."""
    return datetime.datetime.fromtimestamp(
        dt,
        tz=datetime.timezone.utc,
    ).replace(
        microsecond=0,
    )
