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

    async def run(
        self,
        cmd: ICommand[E, R, T],
        app_database: ACID[T] | None,
        max_transactions: int,
    ) -> Result[tuple[R, list[E]], DomainError]:
        """Execute use case and expect a domain error."""
        framework = EzCqrs[R, E]()
        use_case_result = await framework.run(
            cmd=cmd,
            app_database=app_database,
            max_transactions=max_transactions,
        )

        if not isinstance(use_case_result, Ok):
            error = use_case_result.err()
            if not isinstance(error, DomainError):
                msg = f"Encounter error is {error}"
                raise TypeError(msg)
            return Err(error)

        return Ok((use_case_result.unwrap(), framework.published_events()))
