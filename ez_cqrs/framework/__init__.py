"""Ez-Cqrs Framwork."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import E, R
from ez_cqrs.error import DatabaseError, UnexpectedError
from ez_cqrs.typing import T

if TYPE_CHECKING:
    import pydantic
    from result import Result

    from ez_cqrs.acid_exec import ACID
    from ez_cqrs.components import Command
    from ez_cqrs.error import DomainError, ExecutionError
    from ez_cqrs.handler import CommandHandler


@final
@dataclass(repr=True, frozen=True, eq=False)
class EzCqrs(Generic[E, R, T]):
    """EzCqrs framework."""

    cmd_handler: CommandHandler[E, R]

    async def run(
        self,
        cmd: Command[E, R],
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

        ops_registry = OpsRegistry[T](max_lenght=max_transactions)

        validated_or_err = self.cmd_handler.validate(
            command=cmd,
        )
        if not isinstance(validated_or_err, Ok):
            return validated_or_err

        domain_events: list[E] = []
        execution_result_or_err = await self.cmd_handler.handle(
            command=cmd,
            ops_registry=ops_registry,
            event_registry=domain_events,
        )
        execution_err: DomainError | None = None
        if not isinstance(execution_result_or_err, Ok):
            execution_error = execution_result_or_err.err()
            if isinstance(execution_error, UnexpectedError | DatabaseError):
                return Err(execution_error)
            execution_err = execution_error

        commited_or_err = self._commit_existing_transactions(
            max_transactions=max_transactions,
            ops_registry=ops_registry,
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
        ops_registry: OpsRegistry[T],
        app_database: ACID[T] | None,
    ) -> Result[None, DatabaseError]:
        if app_database and max_transactions > 0:
            if ops_registry.storage_length() > 0:
                commited_or_err = app_database.commit_as_transaction(
                    ops_registry=ops_registry,
                )
                if not isinstance(commited_or_err, Ok):
                    return commited_or_err

            if not ops_registry.is_empty():
                msg = "Ops registry didn't came empty after transactions commit."
                raise RuntimeError(msg)
        return Ok(None)
