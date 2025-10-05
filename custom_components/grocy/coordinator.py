"""Data update coordinator for Grocy."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pygrocy2.grocy import Grocy

from .const import (
    CONF_API_KEY,
    CONF_PORT,
    CONF_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    SCAN_INTERVAL,
)
from .grocy_data import GrocyData
from .helpers import extract_base_url_and_path

_LOGGER = logging.getLogger(__name__)


class GrocyDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Grocy data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
    ) -> None:
        """Initialize Grocy data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

        # store the related config entry for entity/device identification
        self.config_entry = config_entry

        url = self.config_entry.data[CONF_URL]
        api_key = self.config_entry.data[CONF_API_KEY]
        port = self.config_entry.data[CONF_PORT]
        verify_ssl = self.config_entry.data[CONF_VERIFY_SSL]

        (base_url, path) = extract_base_url_and_path(url)

        self.grocy_api = Grocy(
            base_url, api_key, path=path, port=port, verify_ssl=verify_ssl
        )
        self.grocy_data = GrocyData(hass, self.grocy_api)

        self.available_entities: List[str] = []
        self.entities: List[Entity] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data."""
        data: dict[str, Any] = {}

        for entity in self.entities:
            if not entity.enabled:
                _LOGGER.debug("Entity %s is disabled.", entity.entity_id)
                continue

            try:
                data[
                    entity.entity_description.key
                ] = await self.grocy_data.async_update_data(
                    entity.entity_description.key
                )
            except Exception as error:  # pylint: disable=broad-except
                raise UpdateFailed(f"Update failed: {error}") from error

        return data

    async def async_force_update_entity(self, entity_key: str) -> None:
        """Force immediate update of an entity by key.

        Finds the first registered entity whose description.key matches
        `entity_key` and forces an immediate state refresh.
        """
        entity = next(
            (
                entity
                for entity in self.entities
                if entity.entity_description.key == entity_key
            ),
            None,
        )
        if entity:
            await entity.async_update_ha_state(force_refresh=True)
