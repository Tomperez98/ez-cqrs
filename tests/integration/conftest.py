"""Conftest for integration testing."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(
    scope="session",
    autouse=True,
)
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Provide an event loop for each async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
