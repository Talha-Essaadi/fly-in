"""Scheduler module for the Fly-in drone routing system.

Handles turn-by-turn drone movement scheduling with collision avoidance,
zone and connection capacity enforcement, and restricted zone 2-turn transit.
"""

from typing import Dict, List, Optional, Tuple
from models import Drone, MapData
from graph import Graph


class DroneState:
    """Tracks the runtime state of a single drone during simulation.

    Attributes:
        drone: The original Drone model object.
        path: Assigned path as list of zone names.
        path_index: Current position index in the path.
        in_transit: Whether the drone is mid-flight to a restricted zone.
        transit_dest: The destination zone if in transit.
        transit_from: The zone the drone left when entering transit.
        delivered: Whether the drone has reached the end zone.
    """

    def __init__(self, drone: Drone, path: List[str]) -> None:
        """Initialize drone state.

        Args:
            drone: The Drone model object.
            path: Assigned path as zone name list.
        """
        self.drone: Drone = drone
        self.path: List[str] = path
        self.path_index: int = 0
        self.in_transit: bool = False
        self.transit_dest: Optional[str] = None
        self.transit_from: Optional[str] = None
        self.delivered: bool = False

    @property
    def current_zone(self) -> str:
        """Return the zone this drone currently occupies."""
        return self.path[self.path_index]

    @property
    def drone_id(self) -> int:
        """Return the drone's ID."""
        return self.drone.id

    def next_zone(self) -> Optional[str]:
        """Return the next zone in the drone's path, or None."""
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None


class Scheduler:
    """Turn-by-turn drone movement scheduler.

    Manages simultaneous drone movements while respecting all capacity
    and zone-type constraints.
    """

    def __init__(self, graph: Graph, map_data: MapData) -> None:
        """Initialize the scheduler.

        Args:
            graph: The Graph object.
            map_data: The parsed map data.
        """
        self.graph: Graph = graph
        self.map_data: MapData = map_data
        self.start: str = graph.start
        self.end: str = graph.end

    def schedule(
        self, drone_paths: List[List[str]]
    ) -> List[List[Tuple[int, str]]]:
        """Run the full turn-by-turn simulation.

        Args:
            drone_paths: List of paths, one per drone.

        Returns:
            List of turns, where each turn is a list of
            (drone_id, destination) movements.
        """
        # Initialize drone states
        states: List[DroneState] = []
        for i, path in enumerate(drone_paths):
            drone: Drone = self.map_data.drones[i]
            states.append(DroneState(drone, path))

        all_turns: List[List[Tuple[int, str]]] = []
        max_iterations: int = 5000

        for _ in range(max_iterations):
            if all(s.delivered for s in states):
                break

            turn_moves: List[Tuple[int, str]] = self._simulate_turn(states)
            if turn_moves:
                all_turns.append(turn_moves)
            elif all(s.delivered for s in states):
                break
            else:
                # No moves possible but not done — deadlock safety
                all_turns.append([])

        return all_turns

    def _simulate_turn(
        self, states: List[DroneState]
    ) -> List[Tuple[int, str]]:
        """Simulate a single turn, resolving all drone movements.

        Args:
            states: List of all drone states.

        Returns:
            List of (drone_id, destination) moves for this turn.
        """
        moves: List[Tuple[int, str]] = []

        # Count current zone occupancy (excluding drones that will move out)
        zone_occupancy: Dict[str, int] = {}
        for s in states:
            if not s.delivered and not s.in_transit:
                zone: str = s.current_zone
                zone_occupancy[zone] = zone_occupancy.get(zone, 0) + 1

        # Track what's being used this turn
        zone_incoming: Dict[str, int] = {}
        zone_outgoing: Dict[str, int] = {}
        conn_usage: Dict[str, int] = {}

        # Phase 1: Handle drones in transit (MUST arrive this turn)
        transit_drones: List[DroneState] = [
            s for s in states if s.in_transit and not s.delivered
        ]
        for s in transit_drones:
            dest: str = s.transit_dest if s.transit_dest else ""
            s.path_index += 1
            s.in_transit = False
            s.drone.zone = dest
            s.transit_dest = None
            s.transit_from = None

            if dest == self.end:
                s.delivered = True

            zone_incoming[dest] = zone_incoming.get(dest, 0) + 1
            moves.append((s.drone_id, dest))

        # Phase 2: Schedule moves for non-transit, non-delivered drones
        # Sort by: shortest remaining path first (greedy priority)
        active: List[DroneState] = [
            s for s in states
            if not s.delivered and not s.in_transit and s.next_zone() is not None
        ]
        active.sort(key=lambda s: len(s.path) - s.path_index)

        for s in active:
            dest = s.next_zone()
            if dest is None:
                continue

            current: str = s.current_zone
            conn = self.graph.get_connection(current, dest)
            if conn is None:
                continue

            dest_zone_type: str = self.graph.zones[dest].zone_type

            # Check connection capacity
            c_key: str = self.graph.connection_key(current, dest)
            current_conn_usage: int = conn_usage.get(c_key, 0)
            if current_conn_usage >= conn.max_link_capacity:
                continue

            if dest_zone_type == "restricted":
                # 2-turn movement: drone enters transit on connection
                conn_usage[c_key] = current_conn_usage + 1
                zone_outgoing[current] = (
                    zone_outgoing.get(current, 0) + 1
                )
                s.in_transit = True
                s.transit_dest = dest
                s.transit_from = current
                # Output shows connection name
                conn_name: str = f"{current}-{dest}"
                moves.append((s.drone_id, conn_name))
            else:
                # 1-turn movement: check destination capacity
                dest_cap: int = self.graph.zone_capacity(dest)
                # Current occupancy at dest
                current_at_dest: int = zone_occupancy.get(dest, 0)
                incoming_at_dest: int = zone_incoming.get(dest, 0)
                outgoing_at_dest: int = zone_outgoing.get(dest, 0)

                # Effective occupancy: current - outgoing + incoming
                effective: int = (
                    current_at_dest - outgoing_at_dest + incoming_at_dest
                )

                # End zone has unlimited capacity
                if dest != self.end and effective >= dest_cap:
                    continue

                # Move the drone
                conn_usage[c_key] = current_conn_usage + 1
                zone_outgoing[current] = (
                    zone_outgoing.get(current, 0) + 1
                )
                zone_incoming[dest] = incoming_at_dest + 1

                s.path_index += 1
                s.drone.zone = dest

                if dest == self.end:
                    s.delivered = True

                moves.append((s.drone_id, dest))

        return moves

    def format_output(
        self, all_turns: List[List[Tuple[int, str]]]
    ) -> str:
        """Format turn data into the required output string.

        Args:
            all_turns: List of turns from schedule().

        Returns:
            Multiline string with one line per turn.
        """
        lines: List[str] = []
        for turn_moves in all_turns:
            if turn_moves:
                parts: List[str] = [
                    f"D{did}-{dest}" for did, dest in turn_moves
                ]
                lines.append(" ".join(parts))
        return "\n".join(lines)
