"""Testing executor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic

from ez_cqrs.aggregate import ERR, Aggregate, C, E, S
from ez_cqrs.testing.validator import AggregateResultValidator

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass
class AggregateTestExecutor(Generic[C, E, ERR, S]):
    """Hold the initial event state of an aggregate and accepts a command."""

    events: list[E]
    services: S | None

    async def when(
        self,
        aggregate_type: type[Aggregate[C, E, ERR, S]],
        command: C,
    ) -> AggregateResultValidator[E, ERR]:
        """Consumes a command and provides a validator object to test against."""
        aggregate = aggregate_type()
        for event in self.events:
            aggregate.apply(event=event)

        result = await aggregate.handle(command=command, services=self.services)
        return AggregateResultValidator(result=result)

    def and_events(self, new_events: list[E]) -> Self:
        """Add additional events to an aggregate test."""
        self.events.extend(new_events)
        return self
