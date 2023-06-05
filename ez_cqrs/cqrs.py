"""Cqrs framework implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic

from result import Err, Ok

from ez_cqrs.aggregate import A, Command, Services
from ez_cqrs.error import AggregateError, UserError
from ez_cqrs.event import E

if TYPE_CHECKING:
    from result import Result
    from typing_extensions import Self

    from ez_cqrs.query import Query
    from ez_cqrs.store import EventStore


@dataclass(repr=False, eq=False)
class CqrsFramework(Generic[A, E]):
    """
    Base framework for applying commands to produce events.

    In [Domain Driven Design](https://en.wikipedia.org/wiki/Domain-driven_design) we
    require that changes are made only after loading the entire `Aggregate` in order to
    ensure that the full context is understood.

    With event-sourcing this means:
    1. Loading all previous events for the aggregate instance.
    2. Applying these events, in order, to a new `Aggregate` in order to reach the
    correct state.
    3. Using the recreated `Aggregate` to handle the inbound `Command` producing events
    or an error.
    4. Persisting any generated events or roll-back in the event of an error.

    To manage these tasks we use the `CqrsFramework`.
    """

    store: EventStore[A, E]
    queries: list[Query[E]]
    service: Services

    def append_query(self, query: Query[E]) -> Self:
        """Append an additional query to the framework."""
        self.queries.append(query)
        return self

    async def execute_with_metadata(
        self,
        aggregate_id: str,
        command: Command,
        metadata: dict[str, str],
    ) -> Result[None, AggregateError]:
        """
        Apply a command to an aggregate.

        Executing a command in this way is the only way to make changes to the state
        of an aggregate in CQRS.

        A `dict[str, str]` is supplied with any contextual information that should be
        associated with this change. This metadata will be attached to any produced
        events and is meant to assist in debugging and auditing. Common information
        might include:
        - time of commit
        - user making the change
        - application version

        An error while processing will result in no events committed and an
        `AggregateError` being returned.

        If successful the events produced will be persisted in the backing `EventStore`
        before being applied to any configured `QueryProcessor`'s
        """
        aggregate_context = await self.store.load_aggregate(aggregate_id=aggregate_id)
        if not isinstance(aggregate_context, Ok):
            return Err(aggregate_context.err())
        aggregate = aggregate_context.unwrap().aggregate()
        resultant_events = await aggregate.handle(
            command=command,
            services=self.service,
        )
        if not isinstance(resultant_events, Ok):
            return Err(UserError(business_violation=resultant_events.err()))
        committed_events = await self.store.commit(
            events=resultant_events.unwrap(),
            context=aggregate_context.unwrap(),
            metadata=metadata,
        )
        if not isinstance(committed_events, Ok):
            return Err(committed_events.err())

        for processor in self.queries:
            await processor.dispatch(
                aggregate_id=aggregate_id,
                events=committed_events.unwrap(),
            )
        return Ok()
