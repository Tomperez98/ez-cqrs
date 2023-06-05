"""Testing framework validator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from result import Ok, Result

from ez_cqrs.aggregate import ERR, E


@dataclass(frozen=True)
class AggregateResultValidator(Generic[E, ERR]):
    """Validator object for the `TestFramework`."""

    result: Result[list[E], ERR]

    def then_expect_events(self, expected_events: list[E]) -> bool:
        """Verify that the expected events have been produced by the command."""
        if not isinstance(self.result, Ok):
            msg = f"Expected success, received aggregate error {self.result.err()}"
            raise TypeError(msg)
        return self.result.unwrap() == expected_events

    def then_expect_error_message(self, error_message: str) -> bool:
        """Verify that the result is a `UserError` and returns the internal error."""
        if isinstance(self.result, Ok):
            msg = f"Expected error, received events {self.result.unwrap()}"
            raise TypeError(msg)
        return str(self.result.err()) == error_message

    def inspect_result(self) -> Result[list[E], ERR]:
        """Return the internal error payload for validation by the user."""
        return self.result
