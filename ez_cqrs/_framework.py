"""EzCQRS framework."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs._typing import T
from ez_cqrs.components import R, StateChanges

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.components import (
        ACID,
        DatabaseError,
        E,
        ExecutionError,
        ICommand,
    )


@final
@dataclass(repr=True, frozen=True, eq=False)
class EzCqrs(Generic[R]):
    """EzCqrs framework."""

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
            execution_error = execution_result_or_err.err()
            return Err(execution_error)

        commited_or_err = self._commit_existing_transactions(
            max_transactions=max_transactions,
            state_changes=state_changes,
            app_database=app_database,
        )
        if not isinstance(commited_or_err, Ok):
            return commited_or_err

        execution_response, domain_events = execution_result_or_err.unwrap()
        event_dispatch_tasks = (event.publish() for event in domain_events)

        asyncio.gather(*event_dispatch_tasks, return_exceptions=False)

        return Ok(execution_response)

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
