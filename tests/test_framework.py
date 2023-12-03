"""Test frameworking using the testing framework."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import BaseModel, Field, ValidationError
from result import Err, Ok

from ez_cqrs import EzCqrs
from ez_cqrs._testing import EzCqrsTester
from ez_cqrs._typing import T
from ez_cqrs.components import (
    Command,
    DomainError,
    DomainEvent,
    UseCaseResponse,
)

if TYPE_CHECKING:
    from result import Result

    from ez_cqrs.components import (
        ExecutionError,
        StateChanges,
    )


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


@dataclass(frozen=True)
class OpenAccountOutput(UseCaseResponse):
    account_id: str


@dataclass(frozen=True)
class DepositMoneyOutput(UseCaseResponse):
    account_id: str
    amount: int


@dataclass(frozen=True)
class OpenAccount(Command[AccountOpened, OpenAccountOutput, T]):
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
        self, state_changes: StateChanges[T]
    ) -> Ok[tuple[OpenAccountOutput, list[AccountOpened]]] | Err[ExecutionError]:
        _ = state_changes
        return Ok(
            (
                OpenAccountOutput(account_id=self.account_id),
                [
                    AccountOpened(
                        account_id=self.account_id,
                        amount=self.amount,
                    ),
                ],
            )
        )


class NegativeDepositAmountError(DomainError):
    def __init__(self, amount: int) -> None:  # noqa: D107
        super().__init__(f"Trying to deposit negative amount {amount}")


@dataclass(frozen=True)
class DepositMoney(Command[MoneyDeposited, DepositMoneyOutput, T]):
    account_id: str
    amount: int

    def validate(self) -> Result[None, ValidationError]:
        class Schema(BaseModel):
            amount: int

        try:
            Schema(amount=self.amount)
        except ValidationError as e:
            return Err(e)
        return Ok()

    async def execute(
        self, state_changes: StateChanges[T]
    ) -> Ok[tuple[DepositMoneyOutput, list[MoneyDeposited]]] | Err[ExecutionError]:
        _ = state_changes
        if self.amount < 0:
            return Err(NegativeDepositAmountError(amount=self.amount))

        return Ok(
            (
                DepositMoneyOutput(
                    account_id=self.account_id,
                    amount=self.amount,
                ),
                [
                    MoneyDeposited(
                        account_id=self.account_id,
                        amount=self.amount,
                    )
                ],
            )
        )


async def test_open_account() -> None:
    """Test open account use case."""
    assert (
        await EzCqrsTester[AccountOpened, OpenAccountOutput, Any](
            framework=EzCqrs[OpenAccountOutput](),
            app_database=None,
        )
        .with_command(OpenAccount(account_id="123", amount=12))
        .expect(
            max_transactions=0, expected_result=Ok(OpenAccountOutput(account_id="123"))
        )
    )


async def test_deposity_money() -> None:
    """Test deposit money use case."""
    assert (
        await EzCqrsTester[MoneyDeposited, DepositMoneyOutput, Any](
            framework=EzCqrs[DepositMoneyOutput](),
            app_database=None,
        )
        .with_command(command=DepositMoney(account_id="123", amount=20))
        .expect(
            max_transactions=0,
            expected_result=Ok(
                DepositMoneyOutput(account_id="123", amount=20),
            ),
        )
    )


async def test_failed_deposity_money() -> None:
    """Test deposit money use case."""
    assert (
        await EzCqrsTester[MoneyDeposited, DepositMoneyOutput, Any](
            framework=EzCqrs[DepositMoneyOutput](),
            app_database=None,
        )
        .with_command(command=DepositMoney(account_id="123", amount=-20))
        .expect(
            max_transactions=0,
            expected_result=Err(NegativeDepositAmountError(amount=-20)),
        )
    )


async def test_without_command() -> None:  # noqa: D103
    with pytest.raises(RuntimeError):
        assert await EzCqrsTester[MoneyDeposited, DepositMoneyOutput, Any](
            framework=EzCqrs[DepositMoneyOutput](), app_database=None
        ).expect(
            max_transactions=0,
            expected_result=Ok(
                DepositMoneyOutput(account_id="123", amount=20),
            ),
        )
