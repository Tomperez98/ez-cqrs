"""Ez-Cqrs Framwork."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar, final

from result import Ok, Result

from ez_cqrs.acid_exec import IRepository, OpsRegistry
from ez_cqrs.components import C, E

if TYPE_CHECKING:
    import pydantic

    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler, EventDispatcher

T = TypeVar("T")


@final
@dataclass(repr=True, frozen=True, eq=False)
class EzCqrs(Generic[C, E]):
    """EzCqrs framework."""

    cmd_handler: CommandHandler[C, E]
    event_dispatcher: EventDispatcher[E]

    async def run(
        self,
        cmd: C,
        max_transactions: int,
        app_database: IRepository | None,
    ) -> Result[Any, ExecutionError | pydantic.ValidationError]:
        """
        Validate and execute command, then dispatch command events.

        Dispatched events are returned to the caller for client specific usage.
        """
        if max_transactions > 0 and not app_database:
            msg = "You are not setting a database to commit transactions"
            raise RuntimeError(msg)

        ops_registry = OpsRegistry[Any](max_lenght=max_transactions)
        event_registry: list[E] = []

        validated_or_err = self.cmd_handler.validate(
            command=cmd,
        )
        if not isinstance(validated_or_err, Ok):
            return validated_or_err

        execution_result_or_err = await asyncio.create_task(
            coro=self.cmd_handler.handle(
                command=cmd,
                ops_registry=ops_registry,
                event_registry=event_registry,
            ),
        )
        if not isinstance(execution_result_or_err, Ok):
            return execution_result_or_err

        if app_database and max_transactions > 0:
            if ops_registry.is_empty():
                msg = "No transactions to commit"
                raise RuntimeError(msg)

            commited_or_err = app_database.commit_as_transaction(
                ops_registry=ops_registry,
            )
            if not isinstance(commited_or_err, Ok):
                return commited_or_err

            if not ops_registry.is_empty():
                msg = "Ops registry didn't came empty after transactions commit."
                raise RuntimeError(msg)

        event_dispatch_tasks = (
            self.event_dispatcher.dispatch(x) for x in event_registry
        )

        asyncio.gather(*event_dispatch_tasks, return_exceptions=False)

        return Ok(execution_result_or_err.unwrap())
