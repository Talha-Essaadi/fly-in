import heapq
from models import Path

class Pathfinding:
    def __init__(self, mapData):
        self.map = mapData
        self.nb_drones = mapData.nb_drones
        self.zones = mapData.zones
        self.connections = mapData.connections
        self.start = mapData.start
        self.end = mapData.end
        self.map_connections = {tuple(sorted([cnn.zone1, cnn.zone2])): cnn for cnn in self.connections}


    def get_neighbors(self, zone):
        zones = set()
        for cnn in self.zones[zone].connections:
            if self.zones[cnn.zone1].zone_type == "blocked" or self.zones[cnn.zone2].zone_type == "blocked":
                continue
            zones.add(cnn.zone1)
            zones.add(cnn.zone2)
        zones.remove(zone)
        return list(zones)


    def get_weight(self, zone):
        if self.zones[zone].zone_type == "restricted":
            return 2
        else:
            return 1


    def get_all_paths(self):
        paths = []
        def dfs(zone, path):
            neighbors = self.get_neighbors(zone)
            for neighbor in neighbors:
                if neighbor in path:
                    continue
                elif neighbor == self.end:
                    path.append(neighbor)
                    break
                dfs(neighbor, path + [neighbor])
            paths.append(path.copy())
        dfs(self.start, [self.start])
        paths = [path for path in paths if path[-1] == self.end]
        return self.compute_flows(paths)


    def compute_flows(self, paths):
        computed_flow = []
        for path in paths:
            computed_flow.append(Path(path=path, max_flow=self.compute_flow(path), turn=self.compute_turn(path)))
        return computed_flow


    def compute_turn(self, path):
        turns = [] 
        for zone1, zone2 in zip(path, path[1:]):
            cnn = self.map_connections[tuple(sorted([zone1, zone2]))]
            max_drones = self.zones[zone2].max_drones
            flow = cnn.max_link_capacity if cnn.max_link_capacity < max_drones else max_drones
            turns.append(self.nb_drones // flow + (1 if self.nb_drones % flow > 0 else 0))
        return turns




    def compute_flow(self, path):
        min_flow = float("inf")
        for zone1, zone2 in zip(path, path[1:]):
            cnn = self.map_connections[tuple(sorted([zone1, zone2]))]
            max_drones = self.zones[zone2].max_drones
            flow = cnn.max_link_capacity if cnn.max_link_capacity < max_drones else max_drones
            if flow < min_flow:
                min_flow = flow
        return min_flow
            

    def find_path(self):
        seen = set()
        pq = []
        dist = {
            self.start: (0, [self.start])
        }
        pq.append(self.start)
        while pq:
            zone = min(pq, key=lambda k: dist[k])
            pq.remove(zone)
            if zone in seen:
                continue
            seen.add(zone)
            # print("neighbors of", zone, ":", self.get_neighbors(zone))
            # print("")
            neighbors = self.get_neighbors(zone)
            for neighbor in neighbors:
                weight = self.get_weight(neighbor)
                if neighbor not in dist:
                    dist[neighbor] = (dist[zone][0] + weight, dist[zone][1] + [neighbor])
                elif dist[zone][0] + weight < dist[neighbor][0]:
                    dist[neighbor] = (dist[zone][0] + weight, dist[zone][1] + [neighbor])
                if neighbor not in seen:
                    pq.append(neighbor)
        return dist