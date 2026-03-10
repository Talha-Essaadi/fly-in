07-03-2026

# Architecture
```sh
fly-in/
│
├── parser/
    ├── __init__.py
    ├── connection.py
    ├── map.py
    ├── parser.py
    ├── zone.py
├── main.py
├── graph.py
├── zone.py
├── connection.py
├── drone.py
├── pathfinding.py
├── scheduler.py
├── simulation.py
└── visualization.py

Map file
   ↓
Read lines
   ↓
Parse drones
   ↓
Parse zones
   ↓
Parse connections
   ↓
Build graph objects
```

# Knowledge:
1. Multi-Agent Pathfinding (MAPF)

# Questions:
1. can the coordomaite be negative
2. what this mean ?
Any metadata block (e.g., [zone=... color=...] for zones, [max_link_capacity=...]
for connections) must be syntactically valid.

3. explain this code:
```py
pattern = r"connection:\s*(\w+)-(\w+)(?:\s*\[(.*)\])?"
match = re.search(pattern, line)

if not match:
   raise ParserError(f"Invalid connection syntax: {line}")

z1, z2, metadata = match.groups()
```

# Project Steps:

```sh
Parser
Graph Structure
djikstra
simulation
Visualization


1 parser
2 graph
3 dijkstra
4 simulation basic
5 multi-path
6 scheduler
7 optimization
```