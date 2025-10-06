"""Entity for Grocy."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
from .coordinator import GrocyDataUpdateCoordinator
from .json_encoder import CustomJSONEncoder


class GrocyEntity(CoordinatorEntity[GrocyDataUpdateCoordinator]):
    """Grocy base entity definition."""

    def __init__(
        self,
        coordinator: GrocyDataUpdateCoordinator,
        description: EntityDescription,
        config_entry: ConfigEntry,
        device_suffix: str | None = None,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_name = description.name
        self._attr_unique_id = f"{config_entry.entry_id}{description.key.lower()}"
        self.entity_description = description
        self._device_suffix = device_suffix

    def _device_identifiers(self, suffix: str | None = None):
        """Return identifiers tuple for the device.

        If suffix is provided, create a secondary device identifier so that
        entities can be grouped under a separate device (e.g., 'chores').
        """
        if suffix:
            return {(DOMAIN, f"{self.coordinator.config_entry.entry_id}-{suffix}")}
        if self._device_suffix:
            return {(DOMAIN, f"{self.coordinator.config_entry.entry_id}-{self._device_suffix}")}
        return {(DOMAIN, self.coordinator.config_entry.entry_id)}

    @property
    def device_info(self) -> DeviceInfo:
        """Grocy device information."""
        # If this entity belongs to a secondary device (e.g. chores), give
        # the device a clearer name like 'Grocy Chores'. Otherwise use the
        # default integration name.
        name = NAME
        if self._device_suffix:
            # Make a simple, human-friendly name; map known suffixes to
            # readable variants.
            if str(self._device_suffix).lower() == "chores":
                name = f"{NAME} Chores"
            else:
                name = f"{NAME} {self._device_suffix.capitalize()}"

        return DeviceInfo(
            identifiers=self._device_identifiers(),
            name=name,
            manufacturer=NAME,
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the extra state attributes."""
        data = self.coordinator.data.get(self.entity_description.key)
        if data and hasattr(self.entity_description, "attributes_fn"):
            return json.loads(
                json.dumps(
                    self.entity_description.attributes_fn(data),
                    cls=CustomJSONEncoder,
                )
            )

        return None
