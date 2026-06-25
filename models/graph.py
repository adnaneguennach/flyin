from typing import List, Dict, Optional
from models.zone import Zone
from models.connection import Connection


class Graph:
    """represents the full drone routing network."""

    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start: Optional[Zone] = None
        self.end: Optional[Zone] = None
        self.nb_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """add a zone to the graph."""
        self.zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        """add a connection to the graph."""
        self.connections.append(connection)

    def get_neighbors(self, zone_name: str) -> List[Zone]:
        """return all neighboring zones of a given zone."""
        neighbors: List[Zone] = []
        for connection in self.connections:
            if connection.zone1.name == zone_name:
                neighbors.append(connection.zone2)
            elif connection.zone2.name == zone_name:
                neighbors.append(connection.zone1)
        return neighbors

    def __repr__(self) -> str:
        return f"Graph(zones={len(self.zones)}, connections={len(self.connections)}, drones={self.nb_drones})"
