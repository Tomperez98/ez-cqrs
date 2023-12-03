"""Test frameworking using the testing framework."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

from pydantic import BaseModel, Field, ValidationError
from result import Err, Ok

from ez_cqrs import EzCqrs
from ez_cqrs._testing import EzCQRSTester
from ez_cqrs._typing import T
from ez_cqrs.components import Command, DomainEvent, UseCaseResponse

if TYPE_CHECKING:
    from result import Result
    from typing_extensions import TypeAlias

    from ez_cqrs.components import ExecutionError, StateChanges


@dataclass(frozen=True)
class AccountOpened(DomainEvent):
    account_id: str
    amount: int

    async def publish(self) -> None:
        ...


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    account_id: str
    amount: int

    async def publish(self) -> None:
        ...


BankAccountEvent: TypeAlias = Union[AccountOpened, MoneyDeposited]


@dataclass(frozen=True)
class OpenAccountOutput(UseCaseResponse):
    account_id: str


@dataclass(frozen=True)
class DepositMoneyOutput(UseCaseResponse):
    account_id: str
    amount: int


BankAccountOutput: TypeAlias = Union[OpenAccountOutput, DepositMoneyOutput]


@dataclass(frozen=True)
class OpenAccount(Command[BankAccountEvent, BankAccountOutput, T]):
    account_id: str
    amount: int

    def validate(self) -> Result[None, ValidationError]:
        class Schema(BaseModel):
            amount: int = Field(gt=0)

        try:
            Schema(amount=self.amount)
        except ValidationError as e:
            return Err(e)
        return Ok()

    async def execute(
        self, events: list[BankAccountEvent], state_changes: StateChanges[T]
    ) -> Ok[BankAccountOutput] | Err[ExecutionError]:
        _ = state_changes
        events.append(
            AccountOpened(
                account_id=self.account_id,
                amount=self.amount,
            ),
        )

        return Ok(OpenAccountOutput(account_id=self.account_id))


@dataclass(frozen=True)
class DepositMoney(Command[BankAccountEvent, BankAccountOutput, T]):
    account_id: str
    amount: int

    def validate(self) -> Result[None, ValidationError]:
        class Schema(BaseModel):
            amount: int = Field(gt=0)

        try:
            Schema(amount=self.amount)
        except ValidationError as e:
            return Err(e)
        return Ok()

    async def execute(
        self, events: list[BankAccountEvent], state_changes: StateChanges[T]
    ) -> Ok[BankAccountOutput] | Err[ExecutionError]:
        _ = state_changes
        events.append(
            MoneyDeposited(
                account_id=self.account_id,
                amount=self.amount,
            ),
        )
        return Ok(
            DepositMoneyOutput(
                account_id=self.account_id,
                amount=self.amount,
            ),
        )


async def test_execution_both_commands() -> None:
    """Test both commands execution."""
    framework_tester = EzCQRSTester[BankAccountEvent, BankAccountOutput, Any](
        framework=EzCqrs[BankAccountEvent, BankAccountOutput, Any](),
        app_database=None,
    )
    framework_tester.with_command(command=OpenAccount(account_id="123", amount=12))
    assert await framework_tester.expect(
        max_transactions=0,
        expected_result=Ok(
            (
                OpenAccountOutput(account_id="123"),
                [AccountOpened(account_id="123", amount=12)],
            )
        ),
    )
    framework_tester.clear()
    framework_tester.with_command(command=DepositMoney(account_id="123", amount=20))
    assert await framework_tester.expect(
        max_transactions=0,
        expected_result=Ok(
            (
                DepositMoneyOutput(account_id="123", amount=20),
                [MoneyDeposited(account_id="123", amount=20)],
            )
        ),
    )
