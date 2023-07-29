"""Test ACID execution."""
from __future__ import annotations

from typing import Any

import pytest

from ez_cqrs.acid_exec import OpsRegistry


@pytest.mark.unit()
class TestOpsRegistry:
    """Test ops registry."""

    def test_is_empty(self) -> None:
        """Test ops registry is empty on creation."""
        ops_registry = OpsRegistry[Any](max_lenght=1)
        assert ops_registry.is_empty()

    def test_add(self) -> None:
        """Test adding values to ops registry."""
        ops_registry = OpsRegistry[Any](max_lenght=1)
        ops_registry.add(value=1)
        assert not ops_registry.is_empty()
        assert ops_registry.storage_length() == 1

    def test_prune_state(self) -> None:
        """Test prune state clears the storage."""
        ops_registry = OpsRegistry[Any](max_lenght=1)
        ops_registry.add(value=1)
        assert not ops_registry.is_empty()
        assert ops_registry.storage_length() == 1
        ops_registry.prune_storage()
        assert ops_registry.is_empty()

    def test_cannot_add_more_that_length(self) -> None:
        """Test adding more values that configured length."""
        ops_registry = OpsRegistry[Any](max_lenght=0)
        with pytest.raises(RuntimeError):
            ops_registry.add(value=1)

    def test_storage_snapshot_new_object(self) -> None:
        """Test get storage snapshot returns a new objected."""
        ops_registry = OpsRegistry[Any](max_lenght=1)
        ops_registry.add(value=1)
        snapshot = ops_registry.storage_snapshot()
        assert id(snapshot) != id(ops_registry.storage_length())
        snapshot.append(10)
        assert len(snapshot) != ops_registry.storage_length()
        assert not ops_registry.is_empty()
        assert ops_registry.storage_length() == 1
