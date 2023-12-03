"""Command handler definition."""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, final

from ez_cqrs.components import E, R

if TYPE_CHECKING:
    import pydantic
    from result import Result

    from ez_cqrs.acid_exec import OpsRegistry
    from ez_cqrs.components import Command
    from ez_cqrs.error import ExecutionError
    from ez_cqrs.typing import T


class CommandHandler(abc.ABC, Generic[E, R]):
    """Command handler handles every command to complete one user intent."""

    @final
    def validate(
        self,
        command: Command[E, R],
    ) -> Result[None, pydantic.ValidationError]:
        """Validate command data."""
        return command.validate()

    @final
    async def handle(
        self,
        command: Command[E, R],
        ops_registry: OpsRegistry[T],
        event_registry: list[E],
    ) -> Result[R, ExecutionError]:
        """
        Consume and process commands.

        The result should be either a vector of events if the command is successful,
        or an error is the command is rejected.

        _All business logic belongs in this method_.
        """
        return await command.execute(events=event_registry, state_changes=ops_registry)
