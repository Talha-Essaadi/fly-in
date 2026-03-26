import heapq

graph = {
    "A": [("B", 8), ("D", 5), ("C", 2)],
    "B": [("A", 8), ("D", 2), ("F", 13)],
    "C": [("A", 2), ("D", 2), ("E", 5)],
    "D": [("A", 5), ("B", 2), ("F", 6), ("G", 3), ("E", 1), ("C", 2)],
    "E": [("C", 5), ("D", 1), ("G", 1)],
    "F": [("B", 13), ("D", 6), ("G", 2), ("H", 3)],
    "G": [("E", 1), ("D", 3), ("F", 2), ("H", 6)],
    "H": [("F", 3), ("G", 6)]
}

def test():
    seen = set()
    pq = []
    dist = {
        "A":0
    }
    pq.append("A")
    while pq:
        node = min(pq, key=lambda k: dist[k])
        pq.remove(node)
        if node in seen:
            continue
        seen.add(node)
        print("node :", node)
        for neighbor, weight in graph[node]:
            print("neighbor:", neighbor)
            if neighbor not in dist:
                dist[neighbor] = dist[node] + weight
            elif dist[node] + weight < dist[neighbor]:
                dist[neighbor] = dist[node] + weight
            if neighbor not in seen:
                pq.append(neighbor)

    print(dist)


def get_neighbors(node):
    neighbors = []
    for neighbor, _ in graph[node]:
        neighbors.append(neighbor)
    return neighbors


def main():
    paths = []
    def dfs(node, path):
        neighbors = get_neighbors(node)
        # print("path:", path)
        # print("neighbors of", node, ":", neighbors)
        for neighbor in neighbors:
            if neighbor in path:
                continue
            # path.append(neighbor)
            if neighbor == "H":
                path.append(neighbor)
                break
            dfs(neighbor, path + [neighbor])
        paths.append(path.copy())
    dfs("A", ["A"])
    paths = [path for path in paths if path[-1] == "H"]
    print(len(paths))





if __name__ == "__main__":
    main()
            


