from models.zone import Zone


class Connection:
    """represents a bidirectional road between two zones."""

    def __init__(
        self,
        zone1: Zone,
        zone2: Zone,
        max_link_capacity: int = 1
    ) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity

    def __repr__(self) -> str:
        return f"connection({self.zone1.name} <-> {self.zone2.name}, max={self.max_link_capacity})"