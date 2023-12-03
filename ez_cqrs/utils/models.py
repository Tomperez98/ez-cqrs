"""Model utilities."""
from __future__ import annotations

import abc
from typing import Any, NewType

DtoPayload = NewType("DtoPayload", dict[str, Any])


class IPersistable(abc.ABC):
    """Entities that implement this interface can be persisted in database."""

    @abc.abstractmethod
    def to_database(self) -> DtoPayload:
        """Prepare entity for database."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_database(cls: type[IPersistable], payload: DtoPayload) -> IPersistable:
        """Instantiate entity from database payload."""
        raise NotImplementedError
