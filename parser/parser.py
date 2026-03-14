import re
from typing import Dict
from models import Zone, Connection, MapData, Drone
from .errors import ParserError


VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


class MapParser:

    def parse(self, file_path: str) -> MapData:

        with open(file_path) as f:
            lines = [line.strip() for line in f]

        if not lines:
            raise ParserError("Empty map file")

        zones: Dict[str, Zone] = {}
        connections: list[Connection] = []

        start = None
        end = None
        first = True
        seen_coordinates = set()
        seen_connections = set()

        for i, line in enumerate(lines, start=1):

            if not line.strip() or line.startswith("#"):
                continue
            if first:
                first = False
                nb_drones = self._parse_drones(line, i)
                continue
            if line.startswith("start_hub:"):
                if start is not None:
                    raise ParserError(f"Multiple start_hub definitions line {i}: {line}")
                zone = self._parse_zone(line, i)
                start = zone.name
                if start in zones:
                    raise ParserError(f"Duplicate zone name {start} line {i}")
                if (zone.x, zone.y) in seen_coordinates:
                    raise ParserError(f"Duplicate coordinates ({zone.x}, {zone.y}) line {i}")
                seen_coordinates.add((zone.x, zone.y))
                zones[zone.name] = zone

            elif line.startswith("end_hub:"):
                if end is not None:
                    raise ParserError(f"Multiple end_hub definitions line {i}: {line}")
                zone = self._parse_zone(line, i)
                end = zone.name
                if end in zones:
                    raise ParserError(f"Duplicate zone name {end} line {i}")
                if (zone.x, zone.y) in seen_coordinates:
                    raise ParserError(f"Duplicate coordinates ({zone.x}, {zone.y}) line {i}")
                seen_coordinates.add((zone.x, zone.y))
                zones[zone.name] = zone

            elif line.startswith("hub:"):
                zone = self._parse_zone(line, i)
                if zone.name in zones:
                    raise ParserError(f"Duplicate zone name {zone.name} line {i}")
                if (zone.x, zone.y) in seen_coordinates:
                    raise ParserError(f"Duplicate coordinates ({zone.x}, {zone.y}) line {i}")
                seen_coordinates.add((zone.x, zone.y))
                zones[zone.name] = zone

            elif line.startswith("connection:"):
                conn = self._parse_connection(line, i, zones)
                if frozenset([conn.zone1, conn.zone2]) in seen_connections:
                    raise ParserError(f"Duplicate connection between {conn.zone1} and {conn.zone2} line {i}")
                seen_connections.add(frozenset([conn.zone1, conn.zone2]))
                connections.append(conn)

            else:
                raise ParserError(f"Invalid line {i}: {line}")

        if start is None or end is None:
            raise ParserError("Map must contain start_hub and end_hub")
        if zones[start].zone_type == "blocked":
            raise ParserError("Start hub cannot be blocked")
        if zones[end].zone_type == "blocked":
            raise ParserError("End hub cannot be blocked")
        for zone in zones.values():
            for conn in connections:
                if conn.zone1 == zone.name or conn.zone2 == zone.name:
                    zone.connections.append(conn)
        return MapData(
            nb_drones=nb_drones,
            drones= [Drone(i+1, start) for i in range(nb_drones)],
            start=start,
            end=end,
            zones=zones,
            connections=connections,
        )

    def _parse_drones(self, line: str, line_number: int) -> int:

        if not line.startswith("nb_drones:"):
            raise ParserError(f"First line must define nb_drones (line {line_number})")

        try:
            nb_drones = int(line.split(":")[1].strip())
            if nb_drones < 1:
                raise ParserError(f"Number of drones must be at least 1 and not negative (line {line_number})")
            return nb_drones
        except ValueError as e:
            raise ParserError(f"Invalid drone number (line {line_number})") from e

    def _parse_zone(self, line: str, line_number: int) -> Zone:

        pattern = r":\s*(\w+)\s+(-?\d+)\s+(-?\d+)(?:\s*\[(.*?)\])?$"
        match = re.search(pattern, line)

        if not match:
            raise ParserError(f"Invalid zone syntax: {line}")

        name, x, y, metadata = match.groups()

        meta = self._parse_metadata(metadata, line, line_number)

        zone_type = meta.get("zone", "normal")

        if zone_type not in VALID_ZONE_TYPES:
            raise ParserError(f"Invalid zone type {zone_type} (line {line_number})")

        max_drones = int(meta.get("max_drones", 1))
        if max_drones < 1:
            raise ParserError(f"Max drones must be positive integer (line {line_number})")

        return Zone(
            name=name,
            x=int(x),
            y=int(y),
            zone_type=zone_type,
            color=meta.get("color"),
            max_drones=max_drones,
        )

    def _parse_connection(
        self,
        line: str,
        line_number: int,
        zones: Dict[str, Zone],
    ) -> Connection:

        pattern = r"connection:\s*(\w+)-(\w+)(?:\s*\[(.*?)\])?$"
        match = re.search(pattern, line)

        if not match:
            raise ParserError(f"Invalid connection syntax: {line} (line {line_number})")

        z1, z2, metadata = match.groups()

        if z1 not in zones or z2 not in zones:
            raise ParserError(f"Connection uses undefined zone: {line} (line {line_number})")

        meta = self._parse_metadata(metadata, line, line_number)

        capacity = int(meta.get("max_link_capacity", 1))
        if capacity < 1:
            raise ParserError(f"Connection capacity must be positive integer (line {line_number})")

        return Connection(z1, z2, capacity)

    def _parse_metadata(self, metadata: str | None, line: str, line_number: int) -> Dict[str, str]:

        if not metadata:
            return {}

        result = {}

        for item in metadata.split():
            if "=" not in item:
                raise ParserError(f"Invalid metadata {item} (line {line_number})")

            key, value = item.split("=", 1)
            if not key or not value:
                raise ParserError(f"Invalid metadata syntax (line {line_number})")
            result[key] = value

        return result