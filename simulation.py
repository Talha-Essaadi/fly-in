from models import Zone, Connection, MapData, Drone
from visualization import Visualizer
from typing import Dict, List

class Simulation:
    """Main simulation engine."""
    def __init__(self, map_data: MapData):
        self.map_data = map_data
        self.drones = map_data.drones
        self.zones = map_data.zones
        self.connections = map_data.connections
        self.start_zone = map_data.start
        self.end_zone = map_data.end
        self.turn = 0


    def run(self):
        """Run the full simulation until all drones reach the end zone."""
        # print("zones :", self.zones)
        visualizer = Visualizer(self.map_data)
        visualizer.run()