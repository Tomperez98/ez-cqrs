"""Testing framework."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from ez_cqrs.aggregate import ERR, C, E, S
from ez_cqrs.testing.executor import AggregateTestExecutor


@dataclass
class Framework(Generic[C, E, ERR, S]):
    """Testing framework."""

    services: S | None

    def given_no_previous_events(self) -> AggregateTestExecutor[C, E, ERR, S]:
        """Initiate an aggregate test with no previous events."""
        return AggregateTestExecutor[C, E, ERR, S](events=[], services=self.services)

    def given(self, events: list[E]) -> AggregateTestExecutor[C, E, ERR, S]:
        """Initiate an aggregate test with a collection of previous events."""
        return AggregateTestExecutor[C, E, ERR, S](
            events=events,
            services=self.services,
        )
