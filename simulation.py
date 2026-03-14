"""Simulation module for the Fly-in drone routing system.

Orchestrates pathfinding, scheduling, output formatting, and visualization.
"""

from models import Zone, Connection, MapData, Drone
from graph import Graph
from pathfinding import Pathfinder
from scheduler import Scheduler
from visualization import Visualizer
from typing import Dict, List, Tuple


class Simulation:
    """Main simulation engine.

    Connects the parser output to the pathfinder, scheduler,
    terminal output, and pygame visualizer.
    """

    def __init__(self, map_data: MapData) -> None:
        """Initialize the simulation.

        Args:
            map_data: The parsed map data.
        """
        self.map_data: MapData = map_data
        self.graph: Graph = Graph(map_data)
        self.pathfinder: Pathfinder = Pathfinder(self.graph)
        self.scheduler: Scheduler = Scheduler(self.graph, map_data)
        self.drones: list[Drone] = map_data.drones
        self.start_zone: str = map_data.start
        self.end_zone: str = map_data.end

    def run(self) -> None:
        """Run the full simulation: pathfind, schedule, output, visualize."""
        nb_drones: int = self.map_data.nb_drones

        # Step 1: Find optimal path assignments
        drone_paths: List[List[str]] = self.pathfinder.assign_drones(
            nb_drones
        )

        if not drone_paths:
            print("Error: No path found from start to end!")
            return

        # Print assigned paths
        print(f"\n{'='*50}")
        print(f"  Fly-in Simulation — {nb_drones} drones")
        print(f"  {self.start_zone} → {self.end_zone}")
        print(f"{'='*50}\n")

        for i, path in enumerate(drone_paths):
            cost: float = self.pathfinder._path_cost(path)
            print(f"  D{i+1}: {' → '.join(path)}  (cost: {cost:.0f})")

        # Step 2: Run turn-by-turn scheduling
        # Reset drone positions before scheduling
        for drone in self.drones:
            drone.zone = self.start_zone

        all_turns: List[List[Tuple[int, str]]] = self.scheduler.schedule(
            drone_paths
        )

        # Step 3: Print simulation output
        print(f"\n{'─'*50}")
        print("  Simulation Output")
        print(f"{'─'*50}\n")

        output: str = self.scheduler.format_output(all_turns)
        print(output)

        # Step 4: Print summary
        total_turns: int = len(
            [t for t in all_turns if t]
        )
        print(f"\n{'─'*50}")
        print(f"  Completed in {total_turns} turns")

        # Secondary metrics
        if total_turns > 0:
            avg_per_drone: float = sum(
                len(p) - 1 for p in drone_paths
            ) / nb_drones
            total_moves: int = sum(len(t) for t in all_turns)
            print(f"  Average path length: {avg_per_drone:.1f}")
            print(f"  Total drone-moves: {total_moves}")
            if total_turns > 0:
                print(
                    f"  Moves per turn: "
                    f"{total_moves / total_turns:.1f}"
                )

        print(f"{'─'*50}\n")

        # Step 5: Reset drone positions and launch visualizer
        for drone in self.drones:
            drone.zone = self.start_zone

        visualizer: Visualizer = Visualizer(self.map_data)
        visualizer.run_simulation(all_turns, drone_paths)
