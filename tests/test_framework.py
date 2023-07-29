"""Test frameworking using the testing framework."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

from pydantic import BaseModel, Field, ValidationError
from result import Err, Ok
from typing_extensions import assert_never

from ez_cqrs.components import Command, DomainEvent, UseCaseOutput
from ez_cqrs.framework import EzCqrs
from ez_cqrs.framework.testing import EzCQRSTester
from ez_cqrs.handler import CommandHandler, EventDispatcher

if TYPE_CHECKING:
    from result import Result
    from typing_extensions import TypeAlias

    from ez_cqrs.acid_exec import OpsRegistry
    from ez_cqrs.error import ExecutionError


@dataclass(frozen=True)
class OpenAccount(Command):
    account_id: str
    amount: int


@dataclass(frozen=True)
class DepositMoney(Command):
    account_id: str
    amount: int


BankAccountCommand: TypeAlias = Union[OpenAccount, DepositMoney]


@dataclass(frozen=True)
class AccountOpened(DomainEvent):
    account_id: str
    amount: int


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    account_id: str
    amount: int


BankAccountEvent: TypeAlias = Union[AccountOpened, MoneyDeposited]


@dataclass(frozen=True)
class OpenAccountOutput(UseCaseOutput):
    account_id: str


@dataclass(frozen=True)
class DepositMoneyOutput(UseCaseOutput):
    account_id: str
    amount: int


BankAccountOutput: TypeAlias = Union[OpenAccountOutput, DepositMoneyOutput]


class BankAccountCommandHandler(
    CommandHandler[BankAccountCommand, BankAccountEvent, BankAccountOutput],
):
    def validate(
        self,
        command: BankAccountCommand,
    ) -> Result[None, ValidationError]:
        if isinstance(command, OpenAccount):

            class OpenAccountValidator(BaseModel):
                amount: int = Field(gt=0)

            try:
                OpenAccountValidator(amount=command.amount)
            except ValidationError as e:
                return Err(e)
            return Ok()
        if isinstance(command, DepositMoney):

            class DepositMoneyValidator(BaseModel):
                amount: int = Field(gt=0)

            try:
                DepositMoneyValidator(amount=command.amount)
            except ValidationError as e:
                return Err(e)
            return Ok()

        assert_never(command)

    async def handle(
        self,
        command: BankAccountCommand,
        ops_registry: OpsRegistry[Any],
        event_registry: list[BankAccountEvent],
    ) -> Result[BankAccountOutput, ExecutionError]:
        _ = ops_registry

        if isinstance(command, OpenAccount):
            event_registry.append(
                AccountOpened(
                    account_id=command.account_id,
                    amount=command.amount,
                ),
            )

            return Ok(OpenAccountOutput(account_id=command.account_id))
        if isinstance(command, DepositMoney):
            event_registry.append(
                MoneyDeposited(
                    account_id=command.account_id,
                    amount=command.amount,
                ),
            )
            return Ok(
                DepositMoneyOutput(
                    account_id=command.account_id,
                    amount=command.amount,
                ),
            )
        assert_never(command)


class BankAccountEventDispatcher(EventDispatcher[BankAccountEvent]):
    async def dispatch(self, event: BankAccountEvent) -> None:
        _ = event


async def test_execution_both_commands() -> None:
    """Test both commands execution."""
    framework_tester = EzCQRSTester[
        BankAccountCommand,
        BankAccountEvent,
        BankAccountOutput,
    ](
        framework=EzCqrs[BankAccountCommand, BankAccountEvent, BankAccountOutput](
            cmd_handler=BankAccountCommandHandler(),
            event_dispatcher=BankAccountEventDispatcher(),
        ),
        app_database=None,
    )
    framework_tester.with_command(command=OpenAccount(account_id="123", amount=12))
    assert await framework_tester.expect(
        max_transactions=0,
        expected_result=Ok(
            OpenAccountOutput(account_id="123"),
        ),
        expected_events=[AccountOpened(account_id="123", amount=12)],
    )
    framework_tester.clear()
    framework_tester.with_command(command=DepositMoney(account_id="123", amount=20))
    assert await framework_tester.expect(
        max_transactions=0,
        expected_result=Ok(
            DepositMoneyOutput(account_id="123", amount=20),
        ),
        expected_events=[MoneyDeposited(account_id="123", amount=20)],
    )
