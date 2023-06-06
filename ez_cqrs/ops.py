"""framework ops."""
from __future__ import annotations

from typing import TYPE_CHECKING

from result import Err, Ok

if TYPE_CHECKING:
    from pydantic import ValidationError
    from result import Result

    from ez_cqrs.components import C, E, V
    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler


async def validate_and_execute_cmd(
    cmd_handler: CommandHandler[C, E, V],
    command: C,
    schema: type[V],
) -> Result[list[E], ExecutionError | ValidationError]:
    """Validate and execute command."""
    validated = cmd_handler.validate(command=command, schema=schema)
    if not isinstance(validated, Ok):
        return Err(validated.err())

    resultant_events = await cmd_handler.handle(command=command)
    if not isinstance(resultant_events, Ok):
        return Err(resultant_events.err())
    return Ok(resultant_events.unwrap())
