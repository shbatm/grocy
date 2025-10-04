"""Integration-style tests for Grocy chore button platform.

These tests are intended to run inside the Home Assistant test harness where
fixtures such as `hass`, `mock_config_entry`, `entity_registry`, and
`aioclient_mock` are available.
"""
from __future__ import annotations

import asyncio

from custom_components.grocy.const import ATTR_CHORES


async def test_chore_buttons_created(
    hass, mock_config_entry, entity_registry, monkeypatch
):
    """Ensure chore button entities are created from chores data."""

    # Add mock config entry and prepare to run setup
    mock_config_entry.add_to_hass(hass)

    # Patch GrocyData.async_update_data to return chores when asked
    async def fake_async_update_data(self, key):
        if key == ATTR_CHORES:
            return [{"chore_id": 123, "chore_name": "Take out trash"}]
        return []

    monkeypatch.setattr(
        "custom_components.grocy.grocy_data.GrocyData.async_update_data",
        fake_async_update_data,
    )

    # Setup the integration
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Wait for coordinator and platform creation
    await asyncio.sleep(0)

    # Inspect entity registry for chore button entity
    entries = entity_registry.async_entries_for_config_entry(mock_config_entry.entry_id)
    chore_buttons = [e for e in entries if e.unique_id and e.unique_id.endswith("chore_button_123")]

    assert len(chore_buttons) == 1
