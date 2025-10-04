class DataUpdateCoordinator:  # pragma: no cover - shim
    def __init__(self, hass, logger=None, name=None, update_interval=None):
        self.hass = hass

    def __class_getitem__(cls, item):
        return cls

class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def __class_getitem__(cls, item):
        return cls


class UpdateFailed(Exception):
    pass
