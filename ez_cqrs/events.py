"""Event base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from mashumaro import DataClassDictMixin


@dataclass(frozen=True)
class DomainEvent(ABC, DataClassDictMixin):
    """
    Domain Event base class.

    A `DomainEvent` represents any business change in the state of an `Aggregate`.
    `DomainEvents` are inmutable, and when [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
    is used they are the single source of truth.
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """A name specifying the event, used for event upcasting."""

    @property
    @abstractmethod
    def event_version(self) -> str:
        """A version of the `event_type`, used for event upcasting."""


E = TypeVar("E", bound=DomainEvent)


@dataclass(frozen=True)
class EventEnvelope(Generic[E]):
    """Data structure that encapsulates an event with its persistent information."""

    aggregate_id: str
    sequence: int
    payload: E
    metadata: dict[str, str]
