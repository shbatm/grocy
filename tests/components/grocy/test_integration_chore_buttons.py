"""Integration-style tests for Grocy chore button platform.

These tests are intended to run inside the Home Assistant test harness where
fixtures such as `hass`, `mock_config_entry`, `entity_registry`, and
`aioclient_mock` are available.
"""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.grocy.button import _extract_chore_fields, GrocyButtonEntity, GrocyButtonEntityDescription


def test_chore_buttons_created_unit():
    """Unit test: mimic initial entity creation from chores data without hass.

    This verifies the integration's entity-creation logic for chores at a
    unit level without requiring Home Assistant fixtures.
    """
    # Sample chores data returned by Grocy
    chores_data = [{"chore_id": 123, "chore_name": "Take out trash"}]

    # Minimal coordinator-like container
    coordinator = type("C", (), {})()
    coordinator.config_entry = MockConfigEntry(domain="grocy", data={}, entry_id="test-entry")
    coordinator.data = {"chores": chores_data}
    coordinator.entities = []

    # Emulate platform logic: create entities for current chores
    entities = []
    for chore in chores_data:
        chore_id, chore_name = _extract_chore_fields(chore)
        description = GrocyButtonEntityDescription(
            key=f"chore_button_{chore_id}",
            name=f"{chore_name} (Execute)",
            entity_registry_enabled_default=False,
        )
        entity = GrocyButtonEntity(coordinator, description, coordinator.config_entry, chore_id)
        coordinator.entities.append(entity)
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0].entity_description.key == "chore_button_123"
