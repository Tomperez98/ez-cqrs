"""
Share state utils.

Shared resources across the program, like third-party application clients,
db connections, or constants should be instantiated in singleton classes and passed to
command handler along with the command itself for execution.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """
    Config exposed global application resources.

    This class in read-only because, once global variables get instantiated, should
    not be modified and only used by command executions.
    """
