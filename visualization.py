import pygame
import math
from models import Zone, Drone, MapData
from typing import Dict, List



class Visualizer:
    def __init__(self, map_data: MapData):
        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w / 2
        self.height = info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("fly-in Simulation")
        self.clock = pygame.time.Clock()
        self.zones = map_data.zones
        self.drones = map_data.drones
        self.connections = map_data.connections
        self.running = True
        self.padding = 80
        min_x = min(zone.x for zone in self.zones.values())
        max_x = max(zone.x for zone in self.zones.values())
        min_y = min(zone.y for zone in self.zones.values())
        max_y = max(zone.y for zone in self.zones.values())
        self.min_x = min_x
        self.min_y = min_y
        range_x = max_x - min_x
        range_y = max_y - min_y
        self.scale_x = (self.width - 2 * self.padding) / range_x if range_x > 0 else 1
        self.scale_y = (self.height - 2 * self.padding) / range_y if range_y > 0 else 1
        self.zone_map: Dict[str, Zone] = {z.name: z for z in self.zones.values()}
        self.zone_radius = self._compute_zone_radius()
        effective_padding = self.padding + self.zone_radius
        self.scale_x = (self.width - 2 * effective_padding) / range_x if range_x > 0 else 1
        self.scale_y = (self.height - 2 * effective_padding) / range_y if range_y > 0 else 1
        self.offset_x = effective_padding
        self.offset_y = effective_padding
        self.selected_zone: Zone | None = None
        self.colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "gray": (128, 128, 128),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128),
            "pink": (255, 192, 203),
            "brown": (165, 42, 42),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "lime": (0, 255, 0),
            "navy": (0, 0, 128),
            "teal": (0, 128, 128),
            "olive": (128, 128, 0),
            "maroon": (128, 0, 0),
            "silver": (192, 192, 192),
            "gold": (255, 215, 0),
            "beige": (245, 245, 220),
            "white": (255, 255, 255),
            "violet": (238, 130, 238)
        }

    def _compute_zone_radius(self) -> int:
        """Compute zone circle radius dynamically based on available space.

        Uses the minimum screen-space distance between any two zones
        so that circles never overlap, clamped to a reasonable range.
        """
        zone_list = list(self.zones.values())
        n = len(zone_list)

        if n <= 1:
            return int(min(self.width, self.height) * 0.1)

        min_dist = float("inf")
        for i in range(n):
            px1 = (zone_list[i].x - self.min_x) * self.scale_x + self.padding
            py1 = (zone_list[i].y - self.min_y) * self.scale_y + self.padding
            for j in range(i + 1, n):
                px2 = (zone_list[j].x - self.min_x) * self.scale_x + self.padding
                py2 = (zone_list[j].y - self.min_y) * self.scale_y + self.padding
                dist = math.hypot(px2 - px1, py2 - py1)
                if dist > 0 and dist < min_dist:
                    min_dist = dist

        radius = int(min_dist * 0.4) if min_dist != float("inf") else 30

        return max(15, min(radius, 80))

    def _zone_screen_pos(self, zone: Zone) -> tuple:
        """Convert a zone's map coordinates to screen pixel position."""
        px = int((zone.x - self.min_x) * self.scale_x + self.offset_x)
        py = int((zone.y - self.min_y) * self.scale_y + self.offset_y)
        return (px, py)

    def draw_connections(self):
        for conn in self.connections:
            z1 = self.zone_map[conn.zone1]
            z2 = self.zone_map[conn.zone2]
            pos1 = self._zone_screen_pos(z1)
            pos2 = self._zone_screen_pos(z2)
            pygame.draw.line(self.screen, (200, 200, 200), pos1, pos2, 2)

    def _get_zone_at(self, mx: int, my: int) -> Zone | None:
        """Return the zone under the mouse position, or None."""
        for zone in self.zones.values():
            px, py = self._zone_screen_pos(zone)
            if math.hypot(mx - px, my - py) <= self.zone_radius:
                return zone
        return None

    def draw_zones(self):
        for zone in self.zones.values():
            color = zone.color if zone.color and zone.color in self.colors else (100, 100, 100)
            px, py = self._zone_screen_pos(zone)
            pygame.draw.circle(self.screen, color, (px, py), self.zone_radius)

    def draw_tooltip(self):
        """Draw a tooltip with zone info next to the selected zone."""
        if self.selected_zone is None:
            return
        zone = self.selected_zone
        px, py = self._zone_screen_pos(zone)
        font = pygame.font.SysFont(None, 24)
        label = f"{zone.name}"
        details = f"zone={zone.zone_type}  max={zone.max_drones}"
        img_name = font.render(label, True, (255, 255, 255))
        img_details = font.render(details, True, (200, 200, 200))
        line_h = img_name.get_height() + 4
        box_w = max(img_name.get_width(), img_details.get_width()) + 16
        box_h = line_h * 2 + 12
        # Position the tooltip above the circle
        tx = px - box_w // 2
        ty = py - self.zone_radius - box_h - 6
        # Keep tooltip inside the window
        tx = max(4, min(tx, int(self.width) - box_w - 4))
        ty = max(4, ty)
        # Background box
        bg_rect = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.screen, (40, 40, 40), bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, width=1, border_radius=6)
        # Highlight the selected circle
        pygame.draw.circle(self.screen, (255, 255, 255), (px, py), self.zone_radius + 3, width=2)
        # Text
        self.screen.blit(img_name, (tx + 8, ty + 6))
        self.screen.blit(img_details, (tx + 8, ty + 6 + line_h))

    def draw_drones(self):
        for drone in self.drones:
            zone = self.zone_map.get(drone.zone)
            if zone:
                px, py = self._zone_screen_pos(zone)
                pygame.draw.circle(self.screen, (255, 0, 0), (px, py), 10)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        clicked = self._get_zone_at(*event.pos)
                        if clicked == self.selected_zone:
                            self.selected_zone = None
                        else:
                            self.selected_zone = clicked
            self.screen.fill((30, 30, 30))
            self.draw_connections()
            self.draw_zones()
            self.draw_drones()
            self.draw_tooltip()
            pygame.display.flip()
            self.clock.tick(60)


    pygame.quit()