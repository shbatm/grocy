class DeviceInfo:  # pragma: no cover - shim
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class DeviceEntryType:
    SERVICE = "service"


class Entity:  # minimal shim
    pass


class EntityDescription:
    def __init__(self, **kwargs):
        self.key = kwargs.get("key")
        self.name = kwargs.get("name")
