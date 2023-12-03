"""Testing framework for EzCQRS framework."""
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from result import Ok

from ez_cqrs.components import E, R
from ez_cqrs.error import DomainError
from ez_cqrs.typing import T

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.acid_exec import ACID
    from ez_cqrs.components import Command, DomainEvent, UseCaseResponse
    from ez_cqrs.framework import EzCqrs


NO_COMMAND_ERROR = "There's not command setted."
CLEAR_ERROR = "Command already set. run `clear()`"


@final
class EzCQRSTester(Generic[E, R, T]):
    """Testing framework for EzCRQS."""

    def __init__(
        self, framework: EzCqrs[E, R, T], app_database: ACID[T] | None
    ) -> None:
        """Test framework for EzCRQS."""
        self.framework = framework
        self.app_database = app_database

        self.command: Command[E, R] | None = None

    def with_command(self, command: Command[E, R]) -> None:
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
        expected_result: Result[tuple[UseCaseResponse, list[DomainEvent]], DomainError],
    ) -> bool:
        """Execute use case and expect a domain error."""
        if self.command is None:
            raise RuntimeError(NO_COMMAND_ERROR)

        use_case_result = await self.framework.run(
            cmd=self.command,
            max_transactions=max_transactions,
            app_database=self.app_database,
        )
        if not isinstance(use_case_result, Ok):
            error = use_case_result.err()
            if not isinstance(error, DomainError):
                msg = f"Encounter error is {error}"
                raise TypeError(msg)

        return all(
            [use_case_result == expected_result],
        )
