class HomeAssistant:  # pragma: no cover - shim for tests
    pass

class ServiceCall:  # pragma: no cover - shim
    def __init__(self, service, data):
        self.service = service
        self.data = data
