"""Command handler definition."""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic

from ez_cqrs.components import C, E, V

if TYPE_CHECKING:
    from pydantic import ValidationError
    from result import Result

    from ez_cqrs.acid_exec import OpsRegistry
    from ez_cqrs.error import ExecutionError
    from ez_cqrs.shared_state import Config


class CommandHandler(abc.ABC, Generic[C, E, V]):
    """Command handler handles every command to complete one user intent."""

    @abc.abstractmethod
    def validate(
        self,
        command: C,
        schema: type[V],
    ) -> Result[None, ValidationError]:
        """Validate command data."""

    @abc.abstractmethod
    async def handle(
        self,
        command: C,
        ops_registry: OpsRegistry[Any],
        config: Config,
    ) -> Result[list[E], ExecutionError]:
        """
        Consume and process commands.

        The result should be either a vector of events if the command is successful,
        or an error is the command is rejected.

        _All business logic belongs in this method_.
        """


class EventDispatcher(abc.ABC, Generic[E]):
    """
    Consumes an dispatches events to downstream services.

    Some examples of tasks that event dispatcher can handle:
    - updated application state views in downstream services.
    - publish events to messaging services.
    """

    @abc.abstractmethod
    async def dispatch(self, event: E, config: Config) -> None:
        """Dispatch events generated by command."""