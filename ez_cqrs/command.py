"""Command base class."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass(frozen=True)
class Command(ABC, DataClassDictMixin):
    """
    Command base class.

    In order to make changes to our system we'll need commands.
    These are the simplest components of any CQRS system and consist
    of little more than packaged data.

    When designing commands an easy mental model to use is that of an
    HTTP API. Each virtual endpoint would receive just the data needed to
    operate that function.
    """
