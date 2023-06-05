"""Event related definition."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from ez_cqrs.aggregate import E


@dataclass(frozen=True)
class EventEnvelope(Generic[E]):
    """
    `EventEnvelope` is a data structure that encapsulates an event.

    All of the associated that will be trasnported and persisted together and will be
    available for queries.

    Within any system an event must be unique based on the compound key composed of its:
    - `aggregate_type`
    - `aggregate_id`
    - `sequence`

    Thus an `EventEnvelope` provides a uniqueness value along with an event `payload`
    and `metadata`.
    """

    aggregate_type: str
    aggregate_id: str
    sequence: int
    payload: E
    metadata: dict[str, str]
