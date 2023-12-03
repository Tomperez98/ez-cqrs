"""EzCQRS framework."""
from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs._typing import T
from ez_cqrs.components import (
    DatabaseError,
    E,
    R,
    UnexpectedError,
)

if TYPE_CHECKING:
    import pydantic
    from result import Result

    from ez_cqrs.components import (
        Command,
        DomainError,
        ExecutionError,
    )


@final
@dataclass
class StateChanges(Generic[T]):
    """
    Operations registry.

    The intended use case for `StateChanges` is to act as an ephemeral
    record of update operations against a database in the execution of a command.

    These update operations would be commited as a single, ACID, transaction agains the
    database before the command execution returns the events recorded.
    """

    max_lenght: int
    _storage: list[T] = field(default_factory=list, init=False)

    def is_empty(self) -> bool:
        """Check `StateChanges` storage is empty."""
        return self.storage_length() == 0

    def add(self, value: T) -> None:
        """Add new value to the storage registry."""
        if len(self._storage) >= self.max_lenght:
            msg = "StateChanges capacity exceeded."
            raise RuntimeError(msg)
        self._storage.append(value)

    def prune_storage(self) -> None:
        """Prune storage."""
        self._storage.clear()

    def storage_snapshot(self) -> list[T]:
        """Get an snapshot of the storage."""
        return self._storage.copy()

    def storage_length(self) -> int:
        """Get storage length."""
        return len(self._storage)


class ACID(abc.ABC, Generic[T]):
    """
    Repository gives acces to the system database layer.

    A database must support transaction operations.

    Besides being the client between the core layer and the persistence layer,
    a system repository is intended to be used right before a command handling
    returns. Before events are returned to the client to be propagated to other
    systems, all update operations recorded during the command execution must be
    commited.
    """

    @abc.abstractmethod
    def commit_as_transaction(
        self,
        ops_registry: StateChanges[T],
    ) -> Result[None, DatabaseError]:
        """
        Commit update operations stored in an `StateChanges`.

        The operation is executed as a transaction againts the database.

        After the commit the ops_registry must be pruned.
        """


@final
@dataclass(repr=True, frozen=True, eq=False)
class EzCqrs(Generic[E, R, T]):
    """EzCqrs framework."""

    async def run(
        self,
        cmd: Command[E, R, T],
        max_transactions: int,
        app_database: ACID[T] | None,
    ) -> Result[tuple[R, list[E]], ExecutionError | pydantic.ValidationError]:
        """
        Validate and execute command, then dispatch command events.

        Dispatched events are returned to the caller for client specific usage.
        """
        if max_transactions > 0 and not app_database:
            msg = "You are not setting a database to commit transactions"
            raise RuntimeError(msg)

        state_changes = StateChanges[T](max_lenght=max_transactions)

        validated_or_err = cmd.validate()
        if not isinstance(validated_or_err, Ok):
            return validated_or_err

        domain_events: list[E] = []
        execution_result_or_err = await cmd.execute(
            events=domain_events, state_changes=state_changes
        )
        execution_err: DomainError | None = None
        if not isinstance(execution_result_or_err, Ok):
            execution_error = execution_result_or_err.err()
            if isinstance(execution_error, (UnexpectedError, DatabaseError)):
                return Err(execution_error)
            execution_err = execution_error

        commited_or_err = self._commit_existing_transactions(
            max_transactions=max_transactions,
            state_changes=state_changes,
            app_database=app_database,
        )
        if not isinstance(commited_or_err, Ok):
            return commited_or_err

        event_dispatch_tasks = (event.publish() for event in domain_events)

        asyncio.gather(*event_dispatch_tasks, return_exceptions=False)

        if execution_err:
            return Err(execution_err)

        return Ok((execution_result_or_err.unwrap(), domain_events))

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
