"""Pathfinding module for the Fly-in drone routing system.

Implements Dijkstra shortest path, K-shortest paths via Yen's algorithm,
Edmonds-Karp max-flow, and flow decomposition for optimal drone distribution.
"""

import heapq
from collections import deque
from typing import Dict, List, Tuple, Optional
from graph import Graph


class Pathfinder:
    """Finds optimal paths and drone distribution through the graph.

    Uses a combination of Dijkstra (weighted shortest paths),
    Yen's K-shortest paths, and Edmonds-Karp max-flow to determine
    the best routing strategy for multiple drones.
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize pathfinder with graph.

        Args:
            graph: The Graph object to pathfind on.
        """
        self.graph: Graph = graph

    def dijkstra(
        self,
        start: str,
        end: str,
        blocked_zones: Optional[set[str]] = None,
        blocked_edges: Optional[set[Tuple[str, str]]] = None,
    ) -> Tuple[List[str], float]:
        """Find the shortest weighted path from start to end.

        Uses a priority queue with zone-type weights. Priority zones
        get a small bonus to be preferred over normal zones at equal cost.

        Args:
            start: Starting zone name.
            end: Destination zone name.
            blocked_zones: Set of zone names to exclude.
            blocked_edges: Set of (z1, z2) edges to exclude.

        Returns:
            Tuple of (path as list of zone names, total cost).
            Returns ([], infinity) if no path exists.
        """
        if blocked_zones is None:
            blocked_zones = set()
        if blocked_edges is None:
            blocked_edges = set()

        # (cost, tiebreaker, zone, path)
        pq: list[Tuple[float, int, str, List[str]]] = [(0.0, 0, start, [start])]
        visited: set[str] = set()
        counter: int = 0

        while pq:
            cost, _, current, path = heapq.heappop(pq)

            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return path, cost

            for neighbor, conn in self.graph.neighbors(current):
                if neighbor in visited or neighbor in blocked_zones:
                    continue
                edge_key: Tuple[str, str] = (current, neighbor)
                rev_key: Tuple[str, str] = (neighbor, current)
                if edge_key in blocked_edges or rev_key in blocked_edges:
                    continue

                move_cost: int = self.graph.move_cost(neighbor)
                # Prefer priority zones via tiny bonus
                zone_type: str = self.graph.zones[neighbor].zone_type
                priority_bonus: float = -0.001 if zone_type == "priority" else 0.0
                new_cost: float = cost + move_cost + priority_bonus

                counter += 1
                heapq.heappush(
                    pq, (new_cost, counter, neighbor, path + [neighbor])
                )

        return [], float("inf")

    def k_shortest_paths(
        self, start: str, end: str, k: int
    ) -> List[Tuple[List[str], float]]:
        """Find up to K shortest paths using Yen's algorithm.

        Args:
            start: Starting zone name.
            end: Destination zone name.
            k: Maximum number of paths to find.

        Returns:
            List of (path, cost) tuples, sorted by cost.
        """
        best_path, best_cost = self.dijkstra(start, end)
        if not best_path:
            return []

        a_paths: List[Tuple[List[str], float]] = [(best_path, best_cost)]
        b_candidates: list[Tuple[float, List[str]]] = []
        seen_paths: set[str] = {",".join(best_path)}

        for _ in range(1, k):
            last_path: List[str] = a_paths[-1][0]

            for i in range(len(last_path) - 1):
                spur_node: str = last_path[i]
                root_path: List[str] = last_path[: i + 1]

                blocked_edges: set[Tuple[str, str]] = set()
                for path, _ in a_paths:
                    if len(path) > i and path[: i + 1] == root_path:
                        blocked_edges.add((path[i], path[i + 1]))

                blocked_zones: set[str] = set(root_path[:-1])

                spur_path, spur_cost = self.dijkstra(
                    spur_node, end, blocked_zones, blocked_edges
                )

                if spur_path:
                    total_path: List[str] = root_path[:-1] + spur_path
                    path_key: str = ",".join(total_path)
                    if path_key not in seen_paths:
                        # Recompute actual cost for the full path
                        total_cost: float = self._path_cost(total_path)
                        heapq.heappush(
                            b_candidates, (total_cost, total_path)
                        )
                        seen_paths.add(path_key)

            if not b_candidates:
                break

            next_cost, next_path = heapq.heappop(b_candidates)
            a_paths.append((next_path, next_cost))

        return a_paths

    def _path_cost(self, path: List[str]) -> float:
        """Compute the weighted cost of a path.

        Args:
            path: List of zone names forming the path.

        Returns:
            Total movement cost.
        """
        cost: float = 0.0
        for i in range(1, len(path)):
            move: int = self.graph.move_cost(path[i])
            zone_type: str = self.graph.zones[path[i]].zone_type
            bonus: float = -0.001 if zone_type == "priority" else 0.0
            cost += move + bonus
        return cost

    def build_flow_network(
        self,
    ) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Dict[str, int]]]:
        """Build a flow network with node-splitting for zone capacity.

        Each zone Z becomes Z_in -> Z_out with capacity = max_drones.
        Connections become Z1_out -> Z2_in with capacity = max_link_capacity.
        Start and end zones have unlimited internal capacity.

        Returns:
            Tuple of (capacity dict, flow dict) for the flow network.
        """
        capacity: Dict[str, Dict[str, int]] = {}
        flow: Dict[str, Dict[str, int]] = {}

        def ensure_node(n: str) -> None:
            if n not in capacity:
                capacity[n] = {}
                flow[n] = {}

        for name, zone in self.graph.zones.items():
            if zone.zone_type == "blocked":
                continue
            n_in: str = f"{name}_in"
            n_out: str = f"{name}_out"
            ensure_node(n_in)
            ensure_node(n_out)

            # Internal capacity (unlimited for start/end)
            if name == self.graph.start or name == self.graph.end:
                cap: int = 10000
            else:
                cap = zone.max_drones
            capacity[n_in][n_out] = cap
            capacity[n_out].setdefault(n_in, 0)
            flow[n_in][n_out] = 0
            flow[n_out][n_in] = 0

        for conn in self.graph.zones.values():
            pass  # zones already handled

        for z1, neighbors in self.graph.adj.items():
            if self.graph.zones[z1].zone_type == "blocked":
                continue
            for z2, conn in neighbors:
                if self.graph.zones[z2].zone_type == "blocked":
                    continue
                src: str = f"{z1}_out"
                dst: str = f"{z2}_in"
                ensure_node(src)
                ensure_node(dst)
                edge_cap: int = conn.max_link_capacity
                capacity[src][dst] = max(
                    capacity[src].get(dst, 0), edge_cap
                )
                capacity[dst].setdefault(src, 0)
                flow[src][dst] = 0
                flow[dst][src] = 0

        return capacity, flow

    def edmonds_karp(self, nb_drones: int) -> int:
        """Compute max-flow from start to end using Edmonds-Karp (BFS).

        Args:
            nb_drones: Total number of drones (upper bound on flow needed).

        Returns:
            The maximum flow value (max drones per turn throughput).
        """
        capacity, flow_net = self.build_flow_network()
        source: str = f"{self.graph.start}_in"
        sink: str = f"{self.graph.end}_out"

        if source not in capacity or sink not in capacity:
            return 0

        total_flow: int = 0

        while total_flow < nb_drones:
            # BFS to find augmenting path
            parent: Dict[str, Optional[str]] = {source: None}
            visited: set[str] = {source}
            queue: deque[str] = deque([source])

            while queue:
                u: str = queue.popleft()
                if u == sink:
                    break
                for v in capacity[u]:
                    residual: int = capacity[u][v] - flow_net[u][v]
                    if v not in visited and residual > 0:
                        visited.add(v)
                        parent[v] = u
                        queue.append(v)

            if sink not in parent:
                break  # No more augmenting paths

            # Find bottleneck
            bottleneck: int = nb_drones - total_flow
            v = sink
            while parent[v] is not None:
                u = parent[v]
                residual = capacity[u][v] - flow_net[u][v]
                bottleneck = min(bottleneck, residual)
                v = u

            # Update flow
            v = sink
            while parent[v] is not None:
                u = parent[v]
                flow_net[u][v] += bottleneck
                flow_net[v][u] -= bottleneck
                v = u

            total_flow += bottleneck

        self._flow_network_cap = capacity
        self._flow_network = flow_net
        self._max_flow = total_flow
        return total_flow

    def decompose_flow_to_paths(
        self,
    ) -> List[Tuple[List[str], int]]:
        """Decompose the max-flow into individual paths with flow amounts.

        Must be called after edmonds_karp().

        Returns:
            List of (path, flow_amount) where path is list of original
            zone names and flow_amount is how many drones use this path.
        """
        capacity = self._flow_network_cap
        flow_net = self._flow_network
        source: str = f"{self.graph.start}_in"
        sink: str = f"{self.graph.end}_out"

        paths: List[Tuple[List[str], int]] = []
        residual_flow: Dict[str, Dict[str, int]] = {
            u: dict(v_map) for u, v_map in flow_net.items()
        }

        while True:
            # DFS to find a path with positive flow
            path_nodes: List[str] = [source]
            visited: set[str] = {source}
            found: bool = False

            while path_nodes:
                current: str = path_nodes[-1]
                if current == sink:
                    found = True
                    break
                moved: bool = False
                for v in capacity[current]:
                    if v not in visited and residual_flow[current][v] > 0:
                        visited.add(v)
                        path_nodes.append(v)
                        moved = True
                        break
                if not moved:
                    path_nodes.pop()

            if not found:
                break

            # Find min flow along path
            min_flow: int = 10000
            for i in range(len(path_nodes) - 1):
                u: str = path_nodes[i]
                v: str = path_nodes[i + 1]
                min_flow = min(min_flow, residual_flow[u][v])

            if min_flow <= 0:
                break

            # Subtract flow
            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i + 1]
                residual_flow[u][v] -= min_flow

            # Convert flow-network node names back to zone names
            zone_path: List[str] = []
            for node in path_nodes:
                zone_name: str = node.rsplit("_", 1)[0]
                if not zone_path or zone_path[-1] != zone_name:
                    zone_path.append(zone_name)

            paths.append((zone_path, min_flow))

        return paths

    def assign_drones(
        self, nb_drones: int
    ) -> List[List[str]]:
        """Compute optimal path assignments for all drones.

        Runs max-flow, decomposes into paths, and assigns drones to paths
        proportionally. Falls back to K-shortest paths if flow is
        insufficient.

        Args:
            nb_drones: Number of drones to route.

        Returns:
            List of paths (one per drone), each path is a list of zone names.
        """
        self.edmonds_karp(nb_drones)
        flow_paths: List[Tuple[List[str], int]] = (
            self.decompose_flow_to_paths()
        )

        if not flow_paths:
            # Fallback: use single shortest path for all drones
            path, _ = self.dijkstra(self.graph.start, self.graph.end)
            if not path:
                return []
            return [list(path) for _ in range(nb_drones)]

        # Sort flow paths by real cost (shorter paths first)
        flow_paths.sort(key=lambda fp: self._path_cost(fp[0]))

        assignments: List[List[str]] = []
        for path, count in flow_paths:
            for _ in range(count):
                assignments.append(list(path))

        # If flow was insufficient, assign remaining to shortest path
        while len(assignments) < nb_drones:
            shortest: List[str] = flow_paths[0][0]
            assignments.append(list(shortest))

        return assignments[:nb_drones]
