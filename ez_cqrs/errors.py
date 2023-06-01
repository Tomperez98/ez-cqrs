"""Error base class."""
from __future__ import annotations


class DomainError(Exception):
    """Raise when a violation of the business rules ocurres."""
