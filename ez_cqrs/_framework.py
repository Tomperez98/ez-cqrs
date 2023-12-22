"""EzCQRS framework."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, final

from result import Ok

from ez_cqrs._typing import T
from ez_cqrs.components import (
    E,
    R,
    StateChanges,
)

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.components import (
        ACID,
        DatabaseError,
        ExecutionError,
        ICommand,
    )


@final
@dataclass(repr=True, frozen=False, eq=False)
class EzCqrs(Generic[R, E]):
    """EzCqrs framework."""

    _published_events: list[E] = field(init=False, default_factory=list)

    async def run(
        self,
        cmd: ICommand[E, R, T],
        max_transactions: int,
        app_database: ACID[T] | None,
    ) -> Result[R, ExecutionError]:
        """
        Validate and execute command, then dispatch command events.

        Dispatched events are returned to the caller for client specific usage.
        """
        if max_transactions > 0 and not app_database:
            msg = "You are not setting a database to commit transactions"
            raise RuntimeError(msg)

        state_changes = StateChanges[T](max_lenght=max_transactions)

        execution_result_or_err = await cmd.execute(state_changes=state_changes)

        if not isinstance(execution_result_or_err, Ok):
            return execution_result_or_err

        commited_or_err = self._commit_existing_transactions(
            max_transactions=max_transactions,
            state_changes=state_changes,
            app_database=app_database,
        )
        if not isinstance(commited_or_err, Ok):
            return commited_or_err

        execution_response, domain_events = execution_result_or_err.unwrap()

        asyncio.gather(*(event.publish() for event in domain_events), return_exceptions=False)

        self._published_events.extend(domain_events)

        return Ok(execution_response)

    def published_events(self) -> list[E]:
        """Get the list of recorded domain events."""
        return self._published_events

    def _commit_existing_transactions(
        self,
        max_transactions: int,
        state_changes: StateChanges[T],
        app_database: ACID[T] | None,
    ) -> Result[None, DatabaseError]:
        if app_database and max_transactions > 0:
            if state_changes.storage_length() > 0:
                commited_or_err = app_database.commit_as_transaction(
                    ops_registry=state_changes,
                )
                if not isinstance(commited_or_err, Ok):
                    return commited_or_err

            if not state_changes.is_empty():
                msg = "Ops registry didn't came empty after transactions commit."
                raise RuntimeError(msg)
        return Ok(None)
