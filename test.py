import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# -----------------
# Graph definition
# -----------------

zones = {
    "start": (100, 300),
    "A": (300, 200),
    "B": (300, 400),
    "C": (500, 300),
    "goal": (700, 300)
}

connections = [
    ("start", "A"),
    ("start", "C"),
    ("start", "B"),
    ("A", "C"),
    ("B", "C"),
    ("C", "goal")
]

# -----------------
# Drone simulation
# -----------------

class Drone:
    def __init__(self, path):
        self.path = path
        self.index = 0
        self.progress = 0

    def update(self):
        if self.index >= len(self.path) - 1:
            return

        self.progress += 0.02

        if self.progress >= 1:
            self.progress = 0
            self.index += 1

    def get_position(self):
        if self.index >= len(self.path) - 1:
            return zones[self.path[-1]]

        start = zones[self.path[self.index]]
        end = zones[self.path[self.index + 1]]

        x = start[0] + (end[0] - start[0]) * self.progress
        y = start[1] + (end[1] - start[1]) * self.progress

        return (x, y)


drones = [
    Drone(["start", "A", "C", "goal"]),
    Drone(["start", "B", "C", "goal"]),
]

# -----------------
# Drawing functions
# -----------------

def draw_graph():
    # connections
    for a, b in connections:
        pygame.draw.line(screen, (200,200,200), zones[a], zones[b], 2)

    # zones
    for name, pos in zones.items():
        pygame.draw.circle(screen, (100,200,255), pos, 20)

        font = pygame.font.SysFont(None, 20)
        text = font.render(name, True, (255,255,255))
        screen.blit(text, (pos[0]-10, pos[1]-35))


def draw_drones():
    for drone in drones:
        x, y = drone.get_position()
        pygame.draw.circle(screen, (255,100,100), (int(x), int(y)), 8)


# -----------------
# Main loop
# -----------------

while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((30,30,30))

    draw_graph()

    for drone in drones:
        drone.update()

    draw_drones()

    pygame.display.flip()
    clock.tick(60)