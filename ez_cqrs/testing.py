"""Testing framework for EzCQRS framework."""
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs._typing import T
from ez_cqrs.components import DomainError, E, R

if TYPE_CHECKING:
    from result import Result
    from typing_extensions import Self

    from ez_cqrs import EzCqrs
    from ez_cqrs.components import ACID, ICommand


NO_COMMAND_ERROR = "There's not command setted."


@final
class EzCqrsTester(Generic[E, R, T]):
    """Testing framework for EzCRQS."""

    def __init__(self, framework: EzCqrs[R], app_database: ACID[T] | None) -> None:
        """Test framework for EzCRQS."""
        self.framework = framework
        self.app_database = app_database

        self.command: ICommand[E, R, T] | None = None

    def with_command(self, command: ICommand[E, R, T]) -> Self:
        """Set command to use for test execution."""
        self.command = command
        return self

    async def expect(
        self,
        max_transactions: int,
        expected_result: Result[R, DomainError],
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

        if isinstance(use_case_result, Ok) and isinstance(expected_result, Ok):
            return use_case_result == expected_result

        if isinstance(use_case_result, Err) and isinstance(expected_result, Err):
            return use_case_result.err().args == expected_result.err().args

        msg = "You are compering a success value against a failure value."
        raise RuntimeError(msg)
