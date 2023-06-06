"""Test handler."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

import pydantic
import pytest
from pydantic import ValidationError
from result import Err, Ok, Result

from ez_cqrs import ops
from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import Command, CommandValidator, DomainEvent
from ez_cqrs.handler import CommandHandler
from ez_cqrs.shared_state import Config

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    from ez_cqrs.error import ExecutionError


@dataclass(frozen=True)
class OpenAccount(Command):  # noqa: D101
    account_id: str
    amount: int


@dataclass(frozen=True)
class DepositMoney(Command):  # noqa: D101
    account_id: str
    amount: int


BankAccountCommand: TypeAlias = Union[OpenAccount, DepositMoney]


class OpenAccountValidator(CommandValidator):  # noqa: D101
    amount: int = pydantic.Field(gt=0)


BankAccountValidator: TypeAlias = OpenAccountValidator


@dataclass(frozen=True)
class AccountOpened(DomainEvent):  # noqa: D101
    account_id: str
    amount: int


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):  # noqa: D101
    account_id: str
    amount: int


BankAccountEvent: TypeAlias = Union[AccountOpened, MoneyDeposited]


class BankAccountCommandHandler(  # noqa: D101
    CommandHandler[BankAccountCommand, BankAccountEvent, BankAccountValidator],
):
    def validate(  # noqa: D102
        self,
        command: BankAccountCommand,
        schema: type[BankAccountValidator],
    ) -> Result[None, ValidationError]:
        try:
            schema(**command.to_dict())
        except ValidationError as e:
            return Err(e)

        return Ok()

    async def handle(  # noqa: D102
        self,
        command: BankAccountCommand,
        ops_registry: OpsRegistry[Any],
        config: Config,
    ) -> Result[list[BankAccountEvent], ExecutionError]:
        _ = ops_registry
        _ = config
        if isinstance(command, OpenAccount):
            return Ok(
                [AccountOpened(account_id=command.account_id, amount=command.amount)],
            )
        if isinstance(command, DepositMoney):
            return Ok(
                [MoneyDeposited(account_id=command.account_id, amount=command.amount)],
            )
        return None


@pytest.mark.integration()
class TestCommandHanlder:  # noqa: D101
    @pytest.mark.parametrize(
        argnames=["command", "validator"],
        argvalues=[
            (OpenAccount(account_id="123", amount=1_000_000), OpenAccountValidator),
        ],
    )
    async def test_validate(
        self,
        command: BankAccountCommand,
        validator: type[BankAccountValidator],
    ) -> None:
        """Test validate method."""
        cmd_handler = BankAccountCommandHandler()

        validated = cmd_handler.validate(
            command=command,
            schema=validator,
        )
        assert validated.unwrap()

    @pytest.mark.parametrize(
        argnames=["command", "expected_events"],
        argvalues=[
            (
                OpenAccount(account_id="123", amount=1_000_000),
                [AccountOpened(account_id="123", amount=1_000_000)],
            ),
        ],
    )
    async def test_handle(
        self,
        command: BankAccountCommand,
        expected_events: list[BankAccountEvent],
    ) -> None:
        """Test handle method."""
        cmd_handler = BankAccountCommandHandler()
        app_config = Config()
        resultant_events = await cmd_handler.handle(
            command=command,
            ops_registry=OpsRegistry[Any](max_lenght=0),
            config=app_config,
        )
        assert resultant_events.unwrap() == expected_events


@pytest.mark.parametrize(
    argnames=["cmd_handler", "cmd", "validator", "expected_events"],
    argvalues=[
        (
            BankAccountCommandHandler(),
            OpenAccount(account_id="123", amount=1),
            OpenAccountValidator,
            [AccountOpened(account_id="123", amount=1)],
        ),
    ],
)
async def test_validate_and_execute_cmd(
    cmd_handler: BankAccountCommandHandler,
    cmd: BankAccountCommand,
    validator: type[BankAccountValidator],
    expected_events: list[BankAccountEvent],
) -> None:
    """Test validate and execution cmd operation."""
    resultant_events = await ops.validate_and_execute_cmd(
        cmd_handler=cmd_handler,
        command=cmd,
        schema=validator,
        max_transactions=0,
        config=Config(),
    )
    assert resultant_events.unwrap() == expected_events
