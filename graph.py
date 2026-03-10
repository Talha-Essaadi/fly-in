

class Graph:
    def __init__(self):
        self.zones = {}
        self.adj = {}

class Drone:
    def __init__(self, id, path):
        self.id = id
        self.path = path
        self.position = 0

class Simulation:

    def run(self):
        while not self.finished():
            self.simulate_turn()

class Simulation:
    drones: list[Drone]
    graph: Graph
    turn: int


class Drone:
    id: int
    current_zone: Zone
    path: list[Zone]

class Connection:
    zone1: Zone
    zone2: Zone
    capacity: int

class Zone:
    name: str
    zone_type: str
    capacity: int
    drones_inside: list

class Graph:
    zones: dict[str, Zone]
    connections: list[Connection]