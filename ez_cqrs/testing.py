"""Testing framework."""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic

from result import Ok, Result

if sys.version_info >= (3, 8):
    from typing import final
else:
    from typing_extensions import final

from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import C, E

if TYPE_CHECKING:
    from typing_extensions import Self

    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler


NO_RESULT_MSG = "No result to evaluate."


@final
@dataclass(frozen=False, repr=False, eq=False)
class CommandHandlerFramework(Generic[C, E]):
    """Testing framework for command hanlder."""

    cmd_handler: CommandHandler[C, E]
    cmd: C

    _result: Result[tuple[Any, list[E]], ExecutionError] | None = field(
        init=False,
        default=None,
    )
    _is_valid: bool | None = field(init=False, default=None)

    def then_expect_is_valid(self) -> bool:
        """Verify command is valid."""
        if not self._is_valid:
            raise RuntimeError(NO_RESULT_MSG)
        return self._is_valid

    def then_expect_is_not_valid(self) -> bool:
        """Verify command is not valid."""
        if not self._is_valid:
            raise RuntimeError(NO_RESULT_MSG)
        return not self._is_valid

    def then_expect_events(self, expected_events: list[E]) -> bool:
        """Verify expected events have been produced by the command."""
        if not self._result:
            raise RuntimeError(NO_RESULT_MSG)
        if not isinstance(self._result, Ok):
            msg = f"expected success, received execution error: {self._result.err()}"
            raise TypeError(msg)
        _, resultant_events = self._result.unwrap()
        return resultant_events == expected_events

    def then_expect_value(self, expected_value: Any) -> bool:  # noqa: ANN401
        """Verify expected value has been produced by the command."""
        if not self._result:
            raise RuntimeError(NO_RESULT_MSG)
        if not isinstance(self._result, Ok):
            msg = f"expected success, received execution error: {self._result.err()}"
            raise TypeError(msg)
        resultant_value, _ = self._result.unwrap()
        return resultant_value == expected_value

    def then_expect_error_message(self, err_msg: str) -> bool:
        """Verify expected error msg have been produced by the command."""
        if not self._result:
            raise RuntimeError(NO_RESULT_MSG)
        if isinstance(self._result, Ok):
            msg = f"expected error, received events: {self._result.unwrap()}"
            raise TypeError(msg)
        return str(self._result.err()) == err_msg

    def inspect_result(self) -> tuple[Any, list[E]]:
        """Inspect execution result."""
        if not self._result:
            raise RuntimeError(NO_RESULT_MSG)

        if not isinstance(self._result, Ok):
            msg = f"expected success, received execution error: {self._result.err()}"
            raise TypeError(msg)

        return self._result.unwrap()

    def validate(
        self,
    ) -> Self:
        """Validate command."""
        validated = self.cmd_handler.validate(
            command=self.cmd,
        )
        if not isinstance(validated, Ok):
            self._is_valid = False
        self._is_valid = True
        return self

    async def execute(
        self,
        max_transactions: int,
    ) -> Self:
        """Execute command while asserting and validating framework's rules."""
        ops_registry = OpsRegistry[Any](max_lenght=max_transactions)
        execution_result = await asyncio.create_task(
            self.cmd_handler.handle(
                command=self.cmd,
                ops_registry=ops_registry,
                event_registry=[],
            ),
        )
        if not ops_registry.is_empty():
            msg = "OpsRegistry is not empty after cmd execution."
            raise RuntimeError(msg)

        self._result = execution_result
        return self
