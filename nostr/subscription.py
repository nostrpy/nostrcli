from .filter import Filters


class Subscription:
    def __init__(self, id: str, filters: Filters = None, batch: int = 0) -> None:
        self.id = id
        self.filters = filters
        self.batch = batch
        self.paused = False

        if not isinstance(self.id, str):
            raise TypeError("Argument 'id' must be of type str")

    def to_json_object(self):
        return {
            "id": self.id,
            "filters": self.filters.to_json_array(),
            "batch": self.batch,
            "paused": self.paused,
        }
