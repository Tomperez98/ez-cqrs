"""Test handler."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

import pydantic
import pytest
from pydantic import BaseModel, ValidationError
from result import Err, Ok, Result
from typing_extensions import assert_never

from ez_cqrs.acid_exec import OpsRegistry
from ez_cqrs.components import Command, DomainEvent
from ez_cqrs.handler import CommandHandler
from ez_cqrs.testing import CommandHandlerFramework

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
    CommandHandler[BankAccountCommand, BankAccountEvent],
):
    def validate(  # noqa: D102
        self,
        command: BankAccountCommand,
    ) -> Result[None, ValidationError]:
        if isinstance(command, OpenAccount):

            class OpenAccountValidator(BaseModel):
                amount: int = pydantic.Field(gt=0)

            try:
                OpenAccountValidator(amount=command.amount)
            except ValidationError as e:
                return Err(e)
            return Ok()
        if isinstance(command, DepositMoney):

            class DepositMoneyValidator(BaseModel):
                amount: int = pydantic.Field(gt=0)

            try:
                DepositMoneyValidator(amount=command.amount)
            except ValidationError as e:
                return Err(e)
            return Ok()

        assert_never(command)

    async def handle(  # noqa: D102
        self,
        command: BankAccountCommand,
        ops_registry: OpsRegistry[Any],
        event_registry: list[BankAccountEvent],
    ) -> Result[tuple[Any, list[BankAccountEvent]], ExecutionError]:
        _ = ops_registry
        _ = event_registry

        if isinstance(command, OpenAccount):
            return Ok(
                (
                    None,
                    [
                        AccountOpened(
                            account_id=command.account_id,
                            amount=command.amount,
                        ),
                    ],
                ),
            )
        if isinstance(command, DepositMoney):
            return Ok(
                (
                    1,
                    [
                        MoneyDeposited(
                            account_id=command.account_id,
                            amount=command.amount,
                        ),
                    ],
                ),
            )
        assert_never(command)


@pytest.mark.integration()
class TestCommandHanlder:  # noqa: D101
    @pytest.mark.parametrize(
        argnames="command",
        argvalues=[
            OpenAccount(account_id="123", amount=1_000_000),
        ],
    )
    async def test_validate(
        self,
        command: BankAccountCommand,
    ) -> None:
        """Test validate method."""
        cmd_handler = BankAccountCommandHandler()

        validated = cmd_handler.validate(
            command=command,
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

        execution_result = await asyncio.create_task(
            cmd_handler.handle(
                command=command,
                ops_registry=OpsRegistry[Any](max_lenght=0),
                event_registry=[],
            ),
        )
        _, resultant_events = execution_result.unwrap()
        assert resultant_events == expected_events

    @pytest.mark.parametrize(
        argnames=["cmd_handler", "cmd", "expected_value", "expected_events"],
        argvalues=[
            (
                BankAccountCommandHandler(),
                OpenAccount(account_id="123", amount=1),
                None,
                [AccountOpened(account_id="123", amount=1)],
            ),
            (
                BankAccountCommandHandler(),
                DepositMoney(account_id="123", amount=1),
                1,
                [MoneyDeposited(account_id="123", amount=1)],
            ),
        ],
    )
    async def test_with_framework(
        self,
        cmd_handler: BankAccountCommandHandler,
        cmd: BankAccountCommand,
        expected_value: Any,  # noqa: ANN401
        expected_events: list[BankAccountEvent],
    ) -> None:
        """Test validate command with testing framework."""
        framework = CommandHandlerFramework[
            BankAccountCommand,
            BankAccountEvent,
        ](
            cmd_handler=cmd_handler,
            cmd=cmd,
        )

        assert framework.validate().then_expect_is_valid()
        await asyncio.create_task(
            framework.execute(
                max_transactions=0,
            ),
        )
        assert framework.then_expect_events(expected_events=expected_events)
        assert framework.then_expect_value(expected_value=expected_value)
        resultant_value, resultant_events = framework.inspect_result()
        assert resultant_value == expected_value
        assert resultant_events == expected_events

    @pytest.mark.parametrize(
        argnames=["cmd_handler", "cmd", "expected_value", "expected_events"],
        argvalues=[
            (
                BankAccountCommandHandler(),
                OpenAccount(account_id="123", amount=1),
                None,
                [AccountOpened(account_id="123", amount=1)],
            ),
            (
                BankAccountCommandHandler(),
                DepositMoney(account_id="123", amount=1),
                1,
                [MoneyDeposited(account_id="123", amount=1)],
            ),
        ],
    )
    async def test_with_framework_without_execute(
        self,
        cmd_handler: BankAccountCommandHandler,
        cmd: BankAccountCommand,
        expected_value: Any,  # noqa: ANN401
        expected_events: list[BankAccountEvent],
    ) -> None:
        """Test validate command with testing framework."""
        framework = CommandHandlerFramework[
            BankAccountCommand,
            BankAccountEvent,
        ](
            cmd_handler=cmd_handler,
            cmd=cmd,
        )

        with pytest.raises(RuntimeError):
            framework.then_expect_is_not_valid()
        with pytest.raises(RuntimeError):
            framework.then_expect_is_valid()
        with pytest.raises(RuntimeError):
            framework.then_expect_events(expected_events=expected_events)
        with pytest.raises(RuntimeError):
            framework.then_expect_value(expected_value=expected_value)
        with pytest.raises(RuntimeError):
            framework.inspect_result()
