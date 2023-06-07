"""framework ops."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from result import Err, Ok

from ez_cqrs.acid_exec import OpsRegistry

if TYPE_CHECKING:
    import pydantic
    from result import Result

    from ez_cqrs.components import C, E
    from ez_cqrs.error import ExecutionError
    from ez_cqrs.handler import CommandHandler
    from ez_cqrs.shared_state import Config


async def validate_and_execute_cmd(
    cmd_handler: CommandHandler[C, E],
    command: C,
    max_transactions: int,
    config: Config,
) -> Result[list[E], ExecutionError | pydantic.ValidationError]:
    """Validate and execute command."""
    validated = cmd_handler.validate(command=command)
    if not isinstance(validated, Ok):
        return Err(validated.err())

    ops_registry = OpsRegistry[Any](max_lenght=max_transactions)
    resultant_events = await cmd_handler.handle(
        command=command,
        ops_registry=ops_registry,
        config=config,
    )
    if not isinstance(resultant_events, Ok):
        return Err(resultant_events.err())

    return Ok(resultant_events.unwrap())
