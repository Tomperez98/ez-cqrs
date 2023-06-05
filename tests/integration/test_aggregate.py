"""Test aggregate."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Union

from result import Ok, Result

from ez_cqrs.aggregate import (
    Aggregate,
    Command,
    DomainError,
    DomainEvent,
    Services,
)
from ez_cqrs.testing import Framework

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

import pytest
from typing_extensions import assert_never


@dataclass(frozen=True)
class OpenBankAccount(Command):
    """Open bank account command."""

    account_id: str
    amount: int


@dataclass(frozen=True)
class DepositMoney(Command):
    """Deposit money into bank account command."""

    account_id: str
    amount: int


BankAccountCommand: TypeAlias = Union[OpenBankAccount, DepositMoney]


@dataclass(frozen=True)
class BankAccountOpened(DomainEvent):
    """Bank account was opened event."""

    account_id: str
    amount: int

    def event_type(self) -> str:  # noqa: D102
        return "BankAccountOpened"

    def event_version(self) -> str:  # noqa: D102
        return "1"


@dataclass(frozen=True)
class MoneyDeposited(DomainEvent):
    """Money deposited into bank account event."""

    account_id: str
    amount: int
    balance: int

    def event_type(self) -> str:  # noqa: D102
        return "MoneyDeposited"

    def event_version(self) -> str:  # noqa: D102
        return "1"


BankAccountEvent: TypeAlias = Union[BankAccountOpened, MoneyDeposited]


class BankAccountServices(Services):
    """Bank account related services."""


class BankAccountAlreadyExistsError(DomainError):
    """Raised when bank account already exists."""


BankAccountError: TypeAlias = BankAccountAlreadyExistsError


@dataclass
class BankAccount(  # noqa: D101
    Aggregate[
        BankAccountCommand,
        BankAccountEvent,
        BankAccountError,
        BankAccountServices,
    ],
):
    account_id: str = field(default="")
    balance: int = field(default=0)

    def aggregate_type(self) -> str:  # noqa: D102
        return "BankAccount"

    async def handle(  # noqa: D102
        self,
        command: BankAccountCommand,
        services: BankAccountServices | None,
    ) -> Result[list[BankAccountEvent], BankAccountError]:
        _ = services
        if isinstance(command, OpenBankAccount):
            return Ok(
                [
                    BankAccountOpened(
                        account_id=command.account_id,
                        amount=command.amount,
                    ),
                ],
            )
        if isinstance(command, DepositMoney):
            return Ok(
                [
                    MoneyDeposited(
                        account_id=command.account_id,
                        amount=command.amount,
                        balance=command.amount + self.balance,
                    ),
                ],
            )
        assert_never(command)

    def apply(  # noqa: D102
        self,
        event: BankAccountEvent,
    ) -> None:
        if isinstance(event, BankAccountOpened):
            self.balance = event.amount

        elif isinstance(event, MoneyDeposited):
            self.balance = event.balance
        else:
            assert_never(event)


@pytest.mark.integration()
class TestBankAccount:
    """Test bank account aggregate."""

    async def test_create_account(self) -> None:
        """Test create account."""
        resultant_events = (
            await Framework[
                BankAccountCommand,
                BankAccountEvent,
                BankAccountError,
                BankAccountServices,
            ](services=None)
            .given_no_previous_events()
            .when(
                aggregate_type=BankAccount,
                command=OpenBankAccount(account_id="123", amount=100),
            )
        )
        assert resultant_events.then_expect_events(
            expected_events=[BankAccountOpened(account_id="123", amount=100)],
        )

    async def test_deposit_money(self) -> None:
        """Test deposit money."""
        resultant_events = (
            await Framework[
                BankAccountCommand,
                BankAccountEvent,
                BankAccountError,
                BankAccountServices,
            ](services=None)
            .given(events=[BankAccountOpened(account_id="123", amount=100)])
            .when(
                aggregate_type=BankAccount,
                command=DepositMoney(account_id="123", amount=50),
            )
        )
        assert resultant_events.then_expect_events(
            expected_events=[MoneyDeposited(account_id="123", amount=50, balance=150)],
        )
