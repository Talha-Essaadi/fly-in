import pygame
import time
import math
from models import Zone, Drone, MapData
from typing import Dict, List



class Visualizer:
    def __init__(self, map_data: MapData):
        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w / 2
        self.height = info.current_h - 100
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("fly-in Simulation")
        self.clock = pygame.time.Clock()
        self.zones = map_data.zones
        self.drones = map_data.drones
        self.connections = map_data.connections
        self.padding = 80
        max_x = max([zone.x for zone in self.zones.values()])
        max_y = max([zone.y for zone in self.zones.values()])
        self.rect_w = (self.width - self.padding * 2) // (max_x + 1)
        self.rect_h = (self.height - self.padding * 2) // (max_y + 1)
        self.raduis = ((self.rect_w // 2) if (self.rect_w < self.rect_h) else (self.rect_h // 2)) * 0.7
        self.running = True
        self.pos = None
        self.speed = 0.05
        self.pause = False
        self.start_zone = map_data.start
        self.end_zone = map_data.end
        self.initialize_map()
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
    
    def initialize_map(self):
        """Initialize the map and place drones in the start zone."""
        self.pause = False
        for i, drone in enumerate(self.drones):
            drone.id = i + 1
            drone.zone = self.start_zone
            drone.t = 0.0
            drone.pos = self._compute_center(self.zones[drone.zone].x, self.zones[drone.zone].y)

    def _compute_center(self, x , y):
        center = ((x * self.rect_w + (self.rect_w // 2)) + self.padding, (y * self.rect_h + (self.rect_h // 2)) + self.padding)
        return center



    def _draw_info(self, zone: Zone) -> None:
        x, y = self._compute_center(zone.x, zone.y)
        rect = pygame.Rect(x - 100, y - 150, 230, 80)
        pygame.draw.rect(self.screen, (40, 40, 40), rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=15)
        font = pygame.font.SysFont(None, 19)
        name = f"Zone: {zone.name}"
        detailed = f"Type: {zone.zone_type}  Max Drones: {zone.max_drones}"
        text = font.render(name, True, (255, 255, 255))
        text_rect = text.get_rect(topleft=(x - 80, y - 130))
        self.screen.blit(text, text_rect)
        text = font.render(detailed, True, (255, 255, 255))
        text_rect = text.get_rect(topleft=(x - 80, y - 100))
        self.screen.blit(text, text_rect)
    
    def _hidden_info(self, zone: Zone) -> None:
        x, y = self._compute_center(zone.x, zone.y)
        pygame.draw.rect(self.screen, (0, 0, 0), (x - 100, y - 150, 230, 80), border_radius=15)


    def _display_info(self) -> None:
        if self.pos is None:
            return
        x, y = self.pos
        for zone in self.zones.values():
            if zone.show_info:
                self._hidden_info(zone)
                zone.show_info = False
        for zone in self.zones.values():
            center = self._compute_center(zone.x, zone.y)
            center_x, center_y = center
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            distance = int(distance)
            if distance <= self.raduis:
                zone.show_info = True
                self._draw_info(zone)


    def draw_zones(self):
        for zone in self.zones.values():
            color = self.colors.get(zone.color, (255, 255, 255))
            center = self._compute_center(zone.x, zone.y)
            pygame.draw.circle(self.screen, color, center , self.raduis)

    def draw_connections(self):
        for cnn in self.connections:
            center_1 = self._compute_center(self.zones[cnn.zone1].x, self.zones[cnn.zone1].y)
            center_2 = self._compute_center(self.zones[cnn.zone2].x, self.zones[cnn.zone2].y)
            pygame.draw.line(self.screen, (255, 255, 255), center_1, center_2, width=2)

    def draw_drones(self):
        for drone in self.drones:
            center = drone.pos
            pygame.draw.circle(self.screen, self.colors["red"], center, self.raduis * 0.4)
            pygame.draw.circle(self.screen, self.colors["white"], center, self.raduis * 0.4, width=1)



    def get_target_zone(self, drone):
        index = drone.path.index(drone.zone) + 1
        return drone.path[index]
        

    def move_drones(self) -> None:
        for drone in self.drones:
            if (drone.zone == self.end_zone):
                continue
            zone_name = self.get_target_zone(drone)
            drone.target_zone = zone_name
            if drone.id != 1:
                drone1 = self.drones[drone.id - 2]
                if zone_name == drone1.target_zone and drone1.zone != self.end_zone:
                    continue
                
            current_zone = self.zones[drone.zone]
            target_zone = self.zones[zone_name]
            x1, y1 = self._compute_center(current_zone.x, current_zone.y)
            x2, y2 = self._compute_center(target_zone.x, target_zone.y)
            if drone.t == 1:
                time.sleep(0.1)
                drone.zone = zone_name
                drone.t = 0.0
                continue
            if drone.t != 1:
                drone.t += self.speed
                if drone.t > 1:
                    drone.t = 1
                x = x1 + (x2 - x1) * drone.t
                y = y1 + (y2 - y1) * drone.t
                drone.pos = (x, y)


    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.initialize_map()
                    elif event.key == pygame.K_EQUALS and (event.mod & pygame.KMOD_SHIFT):
                        self.speed = min(0.05, self.speed + 0.001)
                    elif event.key == pygame.K_MINUS:
                        self.speed = max(0.002, self.speed - 0.001)
                    elif event.key == pygame.K_p:
                        self.pause = False if self.pause else True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.pos = pygame.mouse.get_pos()
            if not self.pause:
                self.screen.fill((0, 0, 0))
                self.draw_connections()
                self.draw_zones()
                self.move_drones()
                self.draw_drones()
                self._display_info()
                self.clock.tick(60)
                pygame.display.flip()


    pygame.quit()