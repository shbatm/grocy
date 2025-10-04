from types import SimpleNamespace

from custom_components.grocy.button import GrocyButtonEntity
from homeassistant.helpers.entity import EntityDescription


class DummyConfigEntry:
    def __init__(self, entry_id: str):
        self.entry_id = entry_id


class DummyCoordinator:
    def __init__(self, entry_id: str, chores):
        self.config_entry = DummyConfigEntry(entry_id)
        self.data = {"chores": chores}


class DummyEntityDesc(EntityDescription):
    pass


def test_button_attributes_from_chore_dict():
    chore = {"chore_id": 42, "chore_name": "Take out trash", "next_estimated_execution_time": None}
    coordinator = DummyCoordinator("test-entry", [chore])
    desc = DummyEntityDesc(key="chore_button_42", name="Take out trash (Execute)")
    entity = GrocyButtonEntity(coordinator, desc, coordinator.config_entry, 42)

    attrs = entity.extra_state_attributes

    assert isinstance(attrs, dict)
    assert attrs.get("chore_id") == 42
    assert attrs.get("chore_name") == "Take out trash"
