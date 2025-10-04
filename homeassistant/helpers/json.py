class ExtendedJSONEncoder:  # pragma: no cover - shim
    def default(self, o):
        raise TypeError()
