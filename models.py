from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Connection:
    zone1: str
    zone2: str
    max_link_capacity: int = 1


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str | None = None
    max_drones: int = 1
    connections: list[Connection] = field(default_factory=list)



@dataclass
class Drone:
    id: int
    zone: str
    path: list[str] = field(default_factory=list)


@dataclass
class MapData:
    nb_drones: int
    drones: list[Drone]
    start: str
    end: str
    zones: Dict[str, Zone]
    connections: list[Connection]

