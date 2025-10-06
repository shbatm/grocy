"""Button platform for Grocy chores."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List
from homeassistant.util import dt as dt_util

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_CHORES, CHORES, DOMAIN, CONF_CREATE_CHORE_BUTTONS
from .coordinator import GrocyDataUpdateCoordinator
from .entity import GrocyEntity
from homeassistant.helpers import entity_registry as er
from .json_encoder import CustomJSONEncoder
import json

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup button platform."""
    coordinator: GrocyDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    entities: List[GrocyButtonEntity] = []

    # Respect the integration option to create chore buttons. Options flow
    # stores the boolean under CONF_CREATE_CHORE_BUTTONS; default to True
    # for backward compatibility.
    # Default to False to respect the options default (opt-in behavior).
    create_buttons = False
    try:
        # Prefer config_entry.options (set via options flow); fall back to
        # config_entry.data for older entries.
        create_buttons = bool(
            config_entry.options.get(CONF_CREATE_CHORE_BUTTONS, config_entry.data.get(CONF_CREATE_CHORE_BUTTONS, False))
        )
    except Exception:
        create_buttons = True

    # Only create buttons if chores are available and the option enables them
    if not create_buttons:
        _LOGGER.debug("Chore button creation disabled via config entry options")
        async_add_entities([], True)
        return

    if ATTR_CHORES in coordinator.available_entities:
        # Read current chores data directly from the GrocyData API and store
        # it on the coordinator. The coordinator only populates `data` for
        # keys that have registered entities, so we need to fetch chores at
        # setup time to create the button entities.
        try:
            chores_data = await coordinator.grocy_data.async_update_data(ATTR_CHORES) or []
        except Exception as err:  # pragma: no cover - best-effort
            _LOGGER.debug("Failed to fetch chores during setup: %s", err)
            chores_data = []

        _LOGGER.debug("Grocy setup: found %d chores", len(chores_data))

        # Cache the fetched chores on the coordinator so the listener can
        # reference coordinator.data[ATTR_CHORES]
        coordinator.data[ATTR_CHORES] = chores_data

        # Create initial entities for current chores
        for chore in chores_data:
            chore_id, chore_name = _extract_chore_fields(chore)
            if chore_id is None:
                _LOGGER.debug("Skipping chore without id: %s", chore)
                continue

            description = GrocyButtonEntityDescription(
                key=f"chore_button_{chore_id}",
                name=f"{chore_name}",
                entity_registry_enabled_default=True,
            )
            # Create the button and request it be grouped under a separate
            # device by passing device_suffix="chores" to the base entity.
            entity = GrocyButtonEntity(
                coordinator, description, config_entry, chore_id, device_suffix="chores"
            )

            coordinator.entities.append(entity)
            entities.append(entity)

    async_add_entities(entities, True)

    # Register a listener to react to coordinator updates and add/remove chore
    # buttons dynamically. This must be defined inside this setup function so
    # it closes over `hass`, `coordinator` and `async_add_entities`.
    def _handle_coordinator_update() -> None:
        """Synchronous listener scheduled by the coordinator.

        The DataUpdateCoordinator invokes listeners synchronously (without
        awaiting), so we must schedule any async work explicitly using
        hass.async_create_task.
        """

        async def _async_work() -> None:
            # Only handle if chores feature is available
            if ATTR_CHORES not in coordinator.available_entities:
                return

            # Coordinator may not populate data for ATTR_CHORES if the
            # chores sensor/entity is disabled. In that case, fetch chores
            # directly so we don't treat a missing key as 'no chores' and
            # remove user-visible button entities incorrectly.
            chores_data = coordinator.data.get(ATTR_CHORES)
            if chores_data is None:
                try:
                    chores_data = await coordinator.grocy_data.async_update_data(ATTR_CHORES) or []
                except Exception as err:  # pragma: no cover - best-effort fetch
                    _LOGGER.debug("Failed to fetch chores during coordinator update: %s", err)
                    chores_data = []

            _LOGGER.debug("Grocy chore update: %d chores present", len(chores_data))

            # Build mapping of existing chore entities in the coordinator
            existing_chore_entities = {
                int(entity.entity_description.key.split("_")[-1]): entity
                for entity in coordinator.entities
                if getattr(entity.entity_description, "key", "").startswith("chore_button_")
            }

            existing_ids = set(existing_chore_entities.keys())
            to_add_ids, to_remove_ids = _compute_chore_diff(existing_ids, chores_data)

            # Add new chore entities
            new_entities: list[GrocyButtonEntity] = []
            for chore in chores_data:
                chore_id, chore_name = _extract_chore_fields(chore)
                if chore_id is None or int(chore_id) not in to_add_ids:
                    continue

                description = GrocyButtonEntityDescription(
                    key=f"chore_button_{chore_id}",
                    name=f"{chore_name} (Execute)",
                    entity_registry_enabled_default=True,
                )
                entity = GrocyButtonEntity(
                    coordinator, description, config_entry, chore_id, device_suffix="chores"
                )
                coordinator.entities.append(entity)
                new_entities.append(entity)
                _LOGGER.debug("Grocy button: prepared entity for chore_id=%s description.key=%s", chore_id, description.key)

            if new_entities:
                _LOGGER.debug("Grocy button: adding %d new entities: %s", len(new_entities), [e.entity_description.key for e in new_entities])
                async_add_entities(new_entities, True)

            # Remove missing chore entities safely
            if to_remove_ids:
                _LOGGER.debug("Grocy button: removing chore ids: %s", to_remove_ids)
                registry = er.async_get(hass)
                for removed_id in to_remove_ids:
                    entity = existing_chore_entities.get(removed_id)
                    if not entity:
                        continue

                    entry = registry.async_get(entity.entity_id)
                    safe_to_remove = False
                    try:
                        expected_prefix = f"{coordinator.config_entry.entry_id}_chore_button_"
                        if entry and entry.unique_id and entry.unique_id.startswith(expected_prefix):
                            # If the registry name differs from the generated name, assume user changed it -> skip
                            generated_name = f"{entity.entity_description.name}"
                            if (not entry.name) or (entry.name == generated_name):
                                disabled_by = getattr(entry, "disabled_by", None)
                                if disabled_by is None:
                                    safe_to_remove = True
                    except Exception:
                        safe_to_remove = False

                    if safe_to_remove:
                        # Keep the registry entry intact and avoid removing the
                        # in-memory entity to prevent UI flicker. Mark the
                        # entity as unavailable so it doesn't appear active.
                        try:
                            # Coordinator entities are instances of our
                            # GrocyButtonEntity; mark them unavailable so the
                            # frontend shows them as not currently usable.
                            setattr(entity, "_attr_available", False)
                        except Exception:
                            # Best-effort: if we can't mark unavailable, just
                            # leave the entity in place and continue.
                            _LOGGER.debug(
                                "Failed to mark entity %s unavailable for chore %s",
                                getattr(entity, "entity_id", "<unknown>"),
                                removed_id,
                            )

        # Schedule the async work without awaiting here
        hass.async_create_task(_async_work())

    # Register the listener with the coordinator
    coordinator.async_add_listener(_handle_coordinator_update)


def _compute_chore_diff(existing_ids: set[int], chores: list[Any]) -> tuple[set[int], set[int]]:
    """Return (to_add_ids, to_remove_ids) based on current chores data.

    - existing_ids: set of chore ids represented in coordinator.entities
    - chores: list of chore items returned by Grocy
    """
    current_ids: set[int] = set()
    for chore in chores:
        cid, _ = _extract_chore_fields(chore)
        if cid is not None:
            current_ids.add(int(cid))

    to_add = current_ids - existing_ids
    to_remove = existing_ids - current_ids
    return to_add, to_remove


def _extract_chore_fields(item) -> tuple[int | None, str]:
    """Return (chore_id, chore_name) for a chore item.

    Handles dict-like data, objects exposing `as_dict()`, and objects
    with attributes. Falls back to scanning common fields.
    """
    # dict-like
    if isinstance(item, dict):
        chore_id = item.get("chore_id") or item.get("id") or item.get("object_id")
        chore_name = item.get("chore_name") or item.get("name") or item.get("title")
        return (chore_id, chore_name or f"Chore {chore_id}")

    # object exposing as_dict()
    if hasattr(item, "as_dict"):
        try:
            d = item.as_dict()
            chore_id = d.get("chore_id") or d.get("id") or d.get("object_id")
            chore_name = d.get("chore_name") or d.get("name") or d.get("title")
            return (chore_id, chore_name or f"Chore {chore_id}")
        except Exception:
            _LOGGER.debug("as_dict() failed on chore item: %s", item)

    # object attributes fallback
    chore_id = getattr(item, "chore_id", None) or getattr(item, "id", None)
    chore_name = getattr(item, "chore_name", None) or getattr(item, "name", None)
    return (chore_id, chore_name or f"Chore {chore_id}")


@dataclass
class GrocyButtonEntityDescription(ButtonEntityDescription):
    """Grocy button entity description."""


class GrocyButtonEntity(GrocyEntity, ButtonEntity):
    """Grocy button entity which executes a chore in Grocy."""

    def __init__(
        self,
        coordinator: GrocyDataUpdateCoordinator,
        description: ButtonEntityDescription,
        config_entry: ConfigEntry,
        chore_id: int,
        device_suffix: str | None = None,
    ) -> None:
        # Allow grouping this entity under a different device by passing
        # device_suffix to the base GrocyEntity.
        super().__init__(coordinator, description, config_entry, device_suffix=device_suffix)
        # Use a clear separator to avoid accidental collisions with other ids
        try:
            self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}_{description.key.lower()}"
        except Exception:
            # Fallback to default unique id behavior from GrocyEntity
            pass
        self._chore_id = chore_id

    async def async_press(self) -> None:
        """Handle the button press to execute the chore."""
        # Execute chore now and refresh the chores entity
        def wrapper():
            # grocy_api.execute_chore(chore_id, done_by, tracked_time, skipped=False)
            self.coordinator.grocy_api.execute_chore(
                self._chore_id, "", dt_util.now(), skipped=False
            )

        await self.hass.async_add_executor_job(wrapper)

        # Force update chores sensor/entity by finding the matching entity and
        # triggering an immediate state refresh. This avoids importing a
        # private helper from `services.py`.
        try:
            entity = next(
                (
                    entity
                    for entity in self.coordinator.entities
                    if entity.entity_description.key == ATTR_CHORES
                ),
                None,
            )
            if entity:
                await entity.async_update_ha_state(force_refresh=True)
        except Exception:  # pragma: no cover - best-effort refresh
            _LOGGER.debug(
                "Failed to force refresh chores after executing chore %s", self._chore_id
            )

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the chore details for this button as attributes.

        Looks up the chore in coordinator.data[ATTR_CHORES] by id and returns
        a JSON-serializable mapping (using CustomJSONEncoder to handle dates).
        """
        chores = self.coordinator.data.get(ATTR_CHORES) or []
        for c in chores:
            try:
                cid, _ = _extract_chore_fields(c)
            except Exception:
                cid = None
            if cid is None:
                continue
            if int(cid) == int(self._chore_id):
                # Prefer as_dict() when available
                if hasattr(c, "as_dict"):
                    try:
                        data = c.as_dict()
                    except Exception:
                        data = c
                else:
                    data = c

                # Ensure the returned structure is JSON-compatible
                try:
                    return json.loads(json.dumps(data, cls=CustomJSONEncoder))
                except Exception:
                    # Best-effort fallback
                    try:
                        return dict(data) if isinstance(data, dict) else {"value": str(data)}
                    except Exception:
                        return None

        return None
