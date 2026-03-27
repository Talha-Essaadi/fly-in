from models import Zone, Connection, MapData, Drone
from visualization import Visualizer
from typing import Dict, List
from pathfinding import Pathfinding

class Simulation:
    """Main simulation engine."""
    def __init__(self, map_data: MapData):
        self.map_data = map_data
        self.nb_drones = map_data.nb_drones
        self.drones = map_data.drones
        self.zones = map_data.zones
        self.connections = map_data.connections
        self.start_zone = map_data.start
        self.end_zone = map_data.end
        self.turn = 0


    def run(self):
        """Run the full simulation until all drones reach the end zone."""
        pathfinding = Pathfinding(self.map_data)
        path_info = pathfinding.find_path()
        l = path_info[self.end_zone][0]
        path = path_info[self.end_zone][1]
        turns = l + self.nb_drones - 1
        output = [""] * turns
        for i, drone in enumerate(self.drones):
            for j, zone in enumerate(path):
                if i + j >= turns:
                    break
                space = "" if len(output[i+j]) == 0 else " "
                output[i+j] = output[i+j] + space + "D" + str(drone.id) + "-" + zone
        for line in output:
            print(line)
        for drone in self.drones:
            drone.path = path
        visualizer = Visualizer(self.map_data)
        visualizer.run()