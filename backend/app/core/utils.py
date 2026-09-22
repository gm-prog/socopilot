
class AttributeDict(dict):
    """Allows dictionary key access via attribute dot notation."""
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(f"'AttributeDict' object has no attribute '{attr}'")

    def __setattr__(self, attr, value):
        self[attr] = value
