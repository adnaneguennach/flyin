from enum import Enum


class ZoneType(Enum):
    """enum representing the type of a zone"""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """represents a location in the drone routing network"""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        max_drones: int = 1,
        color: str = ""
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.color = color

    def __repr__(self) -> str:
        return f"Zone({self.name}, {self.zone_type.value}, max={self.max_drones})"