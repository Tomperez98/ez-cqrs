"""Test commands."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, List, Union

import pytest

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from typing_extensions import assert_never

from ez_cqrs.aggregate import Command


@dataclass(frozen=True)
class Greet(Command):
    """Greet command.."""


@dataclass(frozen=True)
class Walk(Command):
    """Walk command."""

    steps: int


@dataclass(frozen=True)
class ListNames(Command):
    """List names command."""

    names: List[str]  # noqa: UP006


SampleCommands: TypeAlias = Union[Greet, Walk, ListNames]


@pytest.mark.unit()
@pytest.mark.parametrize(
    argnames="command",
    argvalues=[
        Greet(),
        Walk(steps=10),
    ],
)
def test_exhaustive_checking(command: SampleCommands) -> None:
    """Test exhaustive checking works on commands."""
    if isinstance(command, (Walk, Greet, ListNames)):
        assert True
    else:
        assert_never(command)


@pytest.mark.unit()
@pytest.mark.parametrize(
    argnames=[
        "payload",
        "command",
        "expected_command",
    ],
    argvalues=[
        (
            {},
            Greet,
            Greet(),
        ),
        (
            {"steps": 3},
            Walk,
            Walk(steps=3),
        ),
        (
            {"names": ["one", "two", "three"]},
            ListNames,
            ListNames(names=["one", "two", "three"]),
        ),
    ],
)
def test_create_from_dict(
    payload: dict[str, Any],
    command: SampleCommands,
    expected_command: SampleCommands,
) -> None:
    """Create command from payload."""
    command_created = command.from_dict(d=payload)
    assert command_created == expected_command


@pytest.mark.unit()
@pytest.mark.parametrize(
    argnames=[
        "command",
        "expected_payload",
    ],
    argvalues=[
        (
            Greet(),
            {},
        ),
        (
            Walk(steps=3),
            {"steps": 3},
        ),
        (
            ListNames(names=["one", "two", "three"]),
            {"names": ["one", "two", "three"]},
        ),
    ],
)
def test_create_to_dict(
    command: SampleCommands,
    expected_payload: dict[str, Any],
) -> None:
    """Create command from payload."""
    payload_created = command.to_dict()
    assert payload_created == expected_payload
