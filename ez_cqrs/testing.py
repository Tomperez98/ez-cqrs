"""Testing framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic

from result import Ok, Result

from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import C, E, V

if TYPE_CHECKING:
    from typing_extensions import Self

    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler
    from ez_cqrs.shared_state import Config

NO_RESULT_MSG = "No result to evaluate."


@dataclass()
class Framework(Generic[C, E, V]):
    """Testing framework."""

    cmd_handler: CommandHandler[C, E, V]
    cmd: C

    schema_validator: type[V]
    _result: Result[list[E], ExecutionError] | None = field(init=False, default=None)
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
        return self._result.unwrap() == expected_events

    def then_expect_error_message(self, err_msg: str) -> bool:
        """Verify expected error msg have been produced by the command."""
        if not self._result:
            raise RuntimeError(NO_RESULT_MSG)
        if isinstance(self._result, Ok):
            msg = f"expected error, received events: {self._result.unwrap()}"
            raise TypeError(msg)
        return str(self._result.err()) == err_msg

    def validate(
        self,
    ) -> Self:
        """Validate command."""
        validated = self.cmd_handler.validate(
            command=self.cmd,
            schema=self.schema_validator,
        )
        if not isinstance(validated, Ok):
            self._is_valid = False
        self._is_valid = True
        return self

    async def execute(
        self,
        max_transactions: int,
        config: Config,
    ) -> Self:
        """Execute command while asserting and validating framework's rules."""
        ops_registry = OpsRegistry[Any](max_lenght=max_transactions)
        resultant_events = await self.cmd_handler.handle(
            command=self.cmd,
            ops_registry=ops_registry,
            config=config,
        )
        if not ops_registry.is_empty():
            msg = "OpsRegistry is not empty after cmd execution."
            raise RuntimeError(msg)
        self._result = resultant_events
        return self
