class MockRegistryEntry:
    def __init__(self, entity_id, unique_id=None, name=None, disabled_by=None):
        self.entity_id = entity_id
        self.unique_id = unique_id
        self.name = name
        self.disabled_by = disabled_by


class EntityRegistry:
    def __init__(self):
        self._entries = {}

    def async_get(self, entity_id):
        return self._entries.get(entity_id)

    def async_remove(self, entity_id):
        self._entries.pop(entity_id, None)


_REGISTRY = EntityRegistry()


def async_get(hass):
    return _REGISTRY
