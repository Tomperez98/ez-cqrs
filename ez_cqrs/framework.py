"""Ez-Cqrs Framwork."""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic

from result import Err, Ok, Result

from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import C, E

if sys.version_info >= (3, 8):
    from typing import final
else:
    from typing_extensions import final

if TYPE_CHECKING:
    from collections.abc import Coroutine

    import pydantic

    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler, EventDispatcher
    from ez_cqrs.shared_state import Config


@dataclass(repr=True, frozen=True, eq=False)
class EzCqrs(Generic[C, E]):
    """EzCqrs framework."""

    cmd_handler: CommandHandler[C, E]
    event_dispatcher: EventDispatcher[E]

    @final
    async def run(
        self,
        cmd: C,
        max_transactions: int,
        config: Config,
    ) -> Result[list[E], ExecutionError | pydantic.ValidationError]:
        """
        Validate and execute command, then dispatch command events.

        Dispatched events are returned to the caller for client specific usage.
        """
        validated = self.cmd_handler.validate(command=cmd)
        if not isinstance(validated, Ok):
            return Err(validated.err())

        resultant_events = await asyncio.create_task(
            coro=self.cmd_handler.handle(
                command=cmd,
                ops_registry=OpsRegistry[Any](max_lenght=max_transactions),
                config=config,
            ),
        )
        if not isinstance(resultant_events, Ok):
            return Err(resultant_events.err())

        event_dispatch_tasks: list[Coroutine[Any, Any, None]] = []

        list_of_events = resultant_events.unwrap()

        for event in list_of_events:
            event_dispatch_tasks.append(
                self.event_dispatcher.dispatch(event=event, config=config),
            )

        asyncio.gather(*event_dispatch_tasks, return_exceptions=False)

        return Ok(list_of_events)
