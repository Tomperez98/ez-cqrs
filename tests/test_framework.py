"""Test frameworking using the testing framework."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from result import Err, Ok

from ez_cqrs._typing import T
from ez_cqrs.components import (
    DomainError,
    ICommand,
    IDomainEvent,
    IResponse,
)
from ez_cqrs.testing import EzCqrsTester

if TYPE_CHECKING:
    from ez_cqrs.components import (
        ExecutionError,
        StateChanges,
    )


@dataclass(frozen=True)
class AccountOpened(IDomainEvent):
    account_id: str
    amount: int

    async def publish(self) -> None:
        ...


@dataclass(frozen=True)
class MoneyDeposited(IDomainEvent):
    account_id: str
    amount: int

    async def publish(self) -> None:
        ...


@dataclass(frozen=True)
class OpenAccountResponse(IResponse):
    account_id: str


@dataclass(frozen=True)
class DepositMoneyResponse(IResponse):
    account_id: str
    amount: int


@dataclass(frozen=True)
class OpenAccount(ICommand[AccountOpened, OpenAccountResponse, T]):
    account_id: str
    amount: int

    async def execute(
        self, state_changes: StateChanges[T]
    ) -> Ok[tuple[OpenAccountResponse, list[AccountOpened]]] | Err[ExecutionError]:
        _ = state_changes
        return Ok(
            (
                OpenAccountResponse(account_id=self.account_id),
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
class DepositMoney(ICommand[MoneyDeposited, DepositMoneyResponse, T]):
    account_id: str
    amount: int

    async def execute(
        self, state_changes: StateChanges[T]
    ) -> Ok[tuple[DepositMoneyResponse, list[MoneyDeposited]]] | Err[ExecutionError]:
        _ = state_changes
        if self.amount < 0:
            return Err(NegativeDepositAmountError(amount=self.amount))

        return Ok(
            (
                DepositMoneyResponse(
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
    use_case_result = await EzCqrsTester[AccountOpened, OpenAccountResponse, str]().run(
        cmd=OpenAccount(account_id="123", amount=12),
        max_transactions=0,
        app_database=None,
    )
    assert isinstance(use_case_result, Ok)
    _, events = use_case_result.unwrap()
    assert events == [
        AccountOpened(
            account_id="123",
            amount=12,
        )
    ]


async def test_deposity_money() -> None:
    """Test deposit money use case."""
    use_case_result = await EzCqrsTester[MoneyDeposited, DepositMoneyResponse, str]().run(
        cmd=DepositMoney(account_id="123", amount=20),
        max_transactions=0,
        app_database=None,
    )
    assert isinstance(use_case_result, Ok)
    _, events = use_case_result.unwrap()
    assert events == [MoneyDeposited(account_id="123", amount=20)]


async def test_failed_deposity_money() -> None:
    """Test deposit money use case."""
    use_case_result = await EzCqrsTester[MoneyDeposited, DepositMoneyResponse, str]().run(
        cmd=DepositMoney(account_id="123", amount=-20),
        max_transactions=0,
        app_database=None,
    )
    assert isinstance(use_case_result, Err)
