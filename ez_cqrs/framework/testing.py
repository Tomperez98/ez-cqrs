"""Testing framework for EzCQRS framework."""
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from result import Ok

from ez_cqrs.components import C, E
from ez_cqrs.error import DomainError

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.acid_exec import ACID
    from ez_cqrs.components import UseCaseOutput
    from ez_cqrs.framework import EzCqrs


NO_COMMAND_ERROR = "There's not command setted."
CLEAR_ERROR = "Command already set. run `clear()`"
NO_EXECUTION_ERROR = "Run execute before checking results."


@final
class EzCQRSTester(Generic[C, E]):
    """Testing framework for EzCRQS."""

    def __init__(self, framework: EzCqrs[C, E], app_database: ACID | None) -> None:
        """Test framework for EzCRQS."""
        self.framework = framework
        self.app_database = app_database

        self.command: C | None = None

    def with_command(self, command: C) -> None:
        """Set command to use for test execution."""
        if self.command is not None:
            raise RuntimeError(CLEAR_ERROR)
        self.command = command

    def clear(self) -> None:
        """Clean command and use case execution."""
        if self.command is None:
            raise RuntimeError(NO_COMMAND_ERROR)
        self.command = None

    async def expect(
        self,
        max_transactions: int,
        expected_result: Result[UseCaseOutput, DomainError],
        expected_events: list[E],
    ) -> bool:
        """Execute use case and expect a domain error."""
        if self.command is None:
            raise RuntimeError(NO_COMMAND_ERROR)

        event_registry: list[E] = []
        use_case_result = await self.framework.run(
            cmd=self.command,
            max_transactions=max_transactions,
            app_database=self.app_database,
            event_registry=event_registry,
        )
        if not isinstance(use_case_result, Ok):
            error = use_case_result.err()
            if not isinstance(error, DomainError):
                msg = f"Encounter error is {error}"
                raise RuntimeError(msg)

        return all(
            [use_case_result == expected_result, event_registry == expected_events],
        )
