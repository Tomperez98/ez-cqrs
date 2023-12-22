"""Testing framework for EzCQRS framework."""
from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from result import Err, Ok

from ez_cqrs import EzCqrs
from ez_cqrs._typing import T
from ez_cqrs.components import DomainError, E, R

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.components import ACID, ICommand


@final
class EzCqrsTester(Generic[E, R, T]):
    """Testing framework for EzCRQS."""

    def __init__(
        self,
        app_database: ACID[T] | None,
        cmd: ICommand[E, R, T],
        max_transactions: int,
    ) -> None:
        """Test framework for EzCRQS."""
        self.app_database = app_database
        self.cmd = cmd
        self.max_transactions = max_transactions

    async def run(self, expected_events: list[E]) -> Result[R, DomainError]:
        """Execute use case and expect a domain error."""
        framework = EzCqrs[R, E]()
        use_case_result = await framework.run(
            cmd=self.cmd,
            app_database=self.app_database,
            max_transactions=self.max_transactions,
        )
        if expected_events != framework.published_events():
            msg = "Expected events and recorded events does not match."
            raise RuntimeError(msg)

        if not isinstance(use_case_result, Ok):
            error = use_case_result.err()
            if not isinstance(error, DomainError):
                msg = f"Encounter error is {error}"
                raise TypeError(msg)
            return Err(error)

        return use_case_result
