"""Test events."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from ez_cqrs.events import DomainEvent


@pytest.mark.unit()
def test_event_definition() -> None:
    """Test event definition using baseclass."""

    @dataclass(frozen=True)
    class DomainEventCreated(DomainEvent):
        @property
        def event_type(self) -> str:
            return "DomainEventCreated"

        @property
        def event_version(self) -> str:
            return "1.0"

    event = DomainEventCreated()
    assert isinstance(event, DomainEvent)
