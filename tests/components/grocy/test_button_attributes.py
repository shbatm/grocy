from homeassistant.helpers.entity import EntityDescription
from custom_components.grocy.button import GrocyButtonEntity


class DummyEntityDesc(EntityDescription):
    pass


def test_button_attributes_from_chore_dict():
    chore = {"chore_id": 42, "chore_name": "Take out trash", "next_estimated_execution_time": None}
    coordinator = type("C", (), {})()
    coordinator.config_entry = type("E", (), {"entry_id": "test-entry"})()
    coordinator.data = {"chores": [chore]}
    coordinator.entities = []

    desc = DummyEntityDesc(key="chore_button_42", name="Take out trash (Execute)")
    entity = GrocyButtonEntity(coordinator, desc, coordinator.config_entry, 42)

    attrs = entity.extra_state_attributes

    assert isinstance(attrs, dict)
    assert attrs.get("chore_id") == 42
    assert attrs.get("chore_name") == "Take out trash"
