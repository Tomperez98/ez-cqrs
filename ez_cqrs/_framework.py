"""EzCQRS framework."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs._typing import T
from ez_cqrs.components import (
    R,
    StateChanges,
    TransactionExecutionError,
    UnexpectedError,
)

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.components import (
        ACID,
        DomainError,
        E,
        ICommand,
    )


@final
@dataclass(repr=True, frozen=False, eq=False)
class EzCqrs(Generic[R]):
    """EzCqrs framework."""

    async def run(
        self,
        cmd: ICommand[E, R, T],
        max_transactions: int,
        app_database: ACID[T] | None,
        events: list[E],
    ) -> Result[R, DomainError | UnexpectedError | TransactionExecutionError]:
        """
        Validate and execute command, then dispatch command events.

        Dispatched events are returned to the caller for client specific usage.
        """
        if max_transactions > 0 and app_database is None:
            msg = "You are not setting a database to commit transactions"
            raise RuntimeError(msg)

        state_changes = StateChanges[T](max_lenght=max_transactions)
        try:
            execution_result_or_err = await cmd.execute(state_changes=state_changes, events=events)
        except Exception as e:  # noqa: BLE001
            return Err(UnexpectedError(unexpected_error=e))

        if app_database is not None:
            commited_or_err = self._commit_existing_transactions(
                state_changes=state_changes,
                app_database=app_database,
            )

            if not isinstance(commited_or_err, Ok):
                return commited_or_err

        asyncio.gather(*(event.publish() for event in events), return_exceptions=False)

        if not isinstance(execution_result_or_err, Ok):
            return execution_result_or_err

        return Ok(execution_result_or_err.unwrap())

    def _commit_existing_transactions(
        self,
        state_changes: StateChanges[T],
        app_database: ACID[T],
    ) -> Result[None, TransactionExecutionError]:
        if state_changes.storage_length() > 0:
            try:
                app_database.commit_as_transaction(
                    ops_registry=state_changes,
                )
            except Exception as e:  # noqa: BLE001
                return Err(TransactionExecutionError(e))

        if not state_changes.is_empty():
            msg = "Ops registry didn't came empty after transactions commit."
            raise RuntimeError(msg)
        return Ok(None)
