"""Graph module for the Fly-in drone routing system.

Provides an adjacency-list based graph built from parsed MapData,
with helpers for neighbor lookup and movement cost computation.
"""

from models import Zone, Connection, MapData
from typing import Dict, List, Tuple, Optional


# Movement cost by zone type
ZONE_COST: Dict[str, int] = {
    "normal": 1,
    "priority": 1,
    "restricted": 2,
    "blocked": -1,  # inaccessible
}


class Graph:
    """Weighted directed graph built from MapData.

    Attributes:
        zones: Mapping of zone name to Zone object.
        adj: Adjacency list mapping zone name to list of
             (neighbor_name, connection) tuples.
        start: Name of the start zone.
        end: Name of the end zone.
    """

    def __init__(self, map_data: MapData) -> None:
        """Build graph from parsed map data.

        Args:
            map_data: The parsed map data containing zones and connections.
        """
        self.zones: Dict[str, Zone] = map_data.zones
        self.start: str = map_data.start
        self.end: str = map_data.end
        self.adj: Dict[str, List[Tuple[str, Connection]]] = {
            name: [] for name in self.zones
        }
        self._conn_map: Dict[Tuple[str, str], Connection] = {}

        for conn in map_data.connections:
            self.adj[conn.zone1].append((conn.zone2, conn))
            self.adj[conn.zone2].append((conn.zone1, conn))
            self._conn_map[(conn.zone1, conn.zone2)] = conn
            self._conn_map[(conn.zone2, conn.zone1)] = conn

    def neighbors(self, zone_name: str) -> List[Tuple[str, Connection]]:
        """Return reachable neighbors of a zone (excludes blocked zones).

        Args:
            zone_name: The zone to get neighbors for.

        Returns:
            List of (neighbor_name, connection) tuples.
        """
        result: List[Tuple[str, Connection]] = []
        for neighbor, conn in self.adj.get(zone_name, []):
            if self.zones[neighbor].zone_type != "blocked":
                result.append((neighbor, conn))
        return result

    def move_cost(self, dest: str) -> int:
        """Return the movement cost to enter a destination zone.

        Args:
            dest: The destination zone name.

        Returns:
            Number of turns required (1 for normal/priority, 2 for restricted).

        Raises:
            ValueError: If the zone is blocked.
        """
        zone_type: str = self.zones[dest].zone_type
        cost: int = ZONE_COST.get(zone_type, 1)
        if cost < 0:
            raise ValueError(f"Cannot move to blocked zone {dest}")
        return cost

    def get_connection(self, z1: str, z2: str) -> Optional[Connection]:
        """Get the connection object between two zones.

        Args:
            z1: First zone name.
            z2: Second zone name.

        Returns:
            The Connection object, or None if not connected.
        """
        return self._conn_map.get((z1, z2))

    def zone_capacity(self, zone_name: str) -> int:
        """Return the max drone capacity of a zone.

        Args:
            zone_name: The zone to check.

        Returns:
            Maximum number of drones allowed.
        """
        return self.zones[zone_name].max_drones

    def connection_key(self, z1: str, z2: str) -> str:
        """Return a canonical string key for a connection.

        Args:
            z1: First zone name.
            z2: Second zone name.

        Returns:
            A deterministic string key for the connection.
        """
        if z1 < z2:
            return f"{z1}-{z2}"
        return f"{z2}-{z1}"
