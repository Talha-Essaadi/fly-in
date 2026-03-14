import pygame
import math
from models import Zone, Drone, MapData
from typing import Dict, List, Tuple, Optional



# Drone color palette for distinguishing drones
DRONE_COLORS: List[Tuple[int, int, int]] = [
    (255, 80, 80),    # red
    (80, 180, 255),   # blue
    (80, 255, 80),    # green
    (255, 200, 50),   # gold
    (200, 80, 255),   # purple
    (255, 140, 50),   # orange
    (50, 255, 200),   # teal
    (255, 100, 200),  # pink
    (180, 255, 50),   # lime
    (100, 150, 255),  # sky blue
    (255, 80, 180),   # magenta
    (180, 180, 80),   # olive
    (80, 200, 200),   # cyan
    (200, 150, 100),  # tan
    (150, 100, 255),  # violet
]


class Visualizer:
    """Pygame-based visualization for the Fly-in simulation.

    Supports both static graph display and animated step-by-step
    simulation playback with drone movements.
    """

    def __init__(self, map_data: MapData) -> None:
        """Initialize the visualizer.

        Args:
            map_data: The parsed map data.
        """
        pygame.init()
        info: pygame.display.Info = pygame.display.Info()
        self.width: float = info.current_w / 2
        self.height: float = info.current_h
        self.screen: pygame.Surface = pygame.display.set_mode(
            (int(self.width), int(self.height))
        )
        pygame.display.set_caption("Fly-in Simulation")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.zones: Dict[str, Zone] = map_data.zones
        self.drones: list[Drone] = map_data.drones
        self.connections = map_data.connections
        self.start_name: str = map_data.start
        self.end_name: str = map_data.end
        self.running: bool = True
        self.padding: int = 80

        min_x: int = min(zone.x for zone in self.zones.values())
        max_x: int = max(zone.x for zone in self.zones.values())
        min_y: int = min(zone.y for zone in self.zones.values())
        max_y: int = max(zone.y for zone in self.zones.values())
        self.min_x: int = min_x
        self.min_y: int = min_y
        range_x: int = max_x - min_x
        range_y: int = max_y - min_y
        self.scale_x: float = (
            (self.width - 2 * self.padding) / range_x
            if range_x > 0 else 1.0
        )
        self.scale_y: float = (
            (self.height - 2 * self.padding) / range_y
            if range_y > 0 else 1.0
        )
        self.zone_map: Dict[str, Zone] = {
            z.name: z for z in self.zones.values()
        }
        self.zone_radius: int = self._compute_zone_radius()
        effective_padding: float = self.padding + self.zone_radius
        self.scale_x = (
            (self.width - 2 * effective_padding) / range_x
            if range_x > 0 else 1.0
        )
        self.scale_y = (
            (self.height - 2 * effective_padding) / range_y
            if range_y > 0 else 1.0
        )
        self.offset_x: float = effective_padding
        self.offset_y: float = effective_padding
        self.selected_zone: Optional[Zone] = None

        # Simulation playback state
        self.current_turn: int = 0
        self.all_turns: List[List[Tuple[int, str]]] = []
        self.drone_positions: Dict[int, str] = {}
        self.drone_prev_positions: Dict[int, str] = {}
        self.drone_transit: Dict[int, Tuple[str, str]] = {}
        self.delivered: set[int] = set()
        self.paused: bool = False  # auto-play by default
        self.auto_speed: int = 90  # frames per turn (animation duration)
        self.auto_timer: int = 0
        self.simulation_done: bool = False

        # Animation interpolation
        self.animating: bool = False
        self.anim_progress: float = 0.0
        self.anim_speed: float = 0.02  # progress per frame (0..1)
        self.anim_moves: List[Tuple[int, str]] = []  # moves being animated

        self.font: pygame.font.Font = pygame.font.SysFont(None, 20)
        self.font_large: pygame.font.Font = pygame.font.SysFont(None, 28)
        self.font_hud: pygame.font.Font = pygame.font.SysFont(None, 22)

        self.colors: Dict[str, Tuple[int, int, int]] = {
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
            "violet": (238, 130, 238),
        }

    def _compute_zone_radius(self) -> int:
        """Compute zone circle radius dynamically based on available space.

        Returns:
            Radius in pixels, clamped between 15 and 80.
        """
        zone_list: list[Zone] = list(self.zones.values())
        n: int = len(zone_list)

        if n <= 1:
            return int(min(self.width, self.height) * 0.1)

        min_dist: float = float("inf")
        for i in range(n):
            px1: float = (
                (zone_list[i].x - self.min_x) * self.scale_x + self.padding
            )
            py1: float = (
                (zone_list[i].y - self.min_y) * self.scale_y + self.padding
            )
            for j in range(i + 1, n):
                px2: float = (
                    (zone_list[j].x - self.min_x) * self.scale_x
                    + self.padding
                )
                py2: float = (
                    (zone_list[j].y - self.min_y) * self.scale_y
                    + self.padding
                )
                dist: float = math.hypot(px2 - px1, py2 - py1)
                if 0 < dist < min_dist:
                    min_dist = dist

        radius: int = (
            int(min_dist * 0.4) if min_dist != float("inf") else 30
        )
        return max(15, min(radius, 80))

    def _zone_screen_pos(self, zone: Zone) -> Tuple[int, int]:
        """Convert a zone's map coordinates to screen pixel position.

        Args:
            zone: The Zone object.

        Returns:
            Tuple of (x, y) pixel coordinates.
        """
        px: int = int(
            (zone.x - self.min_x) * self.scale_x + self.offset_x
        )
        py: int = int(
            (zone.y - self.min_y) * self.scale_y + self.offset_y
        )
        return (px, py)

    def _get_zone_at(self, mx: int, my: int) -> Optional[Zone]:
        """Return the zone under the mouse position, or None.

        Args:
            mx: Mouse x position.
            my: Mouse y position.

        Returns:
            Zone object if mouse is within radius, else None.
        """
        for zone in self.zones.values():
            px, py = self._zone_screen_pos(zone)
            if math.hypot(mx - px, my - py) <= self.zone_radius:
                return zone
        return None

    def _drone_color(self, drone_id: int) -> Tuple[int, int, int]:
        """Get a unique color for a drone.

        Args:
            drone_id: The drone's ID (1-based).

        Returns:
            RGB color tuple.
        """
        idx: int = (drone_id - 1) % len(DRONE_COLORS)
        return DRONE_COLORS[idx]

    def draw_connections(self) -> None:
        """Draw all connections between zones."""
        for conn in self.connections:
            z1: Zone = self.zone_map[conn.zone1]
            z2: Zone = self.zone_map[conn.zone2]
            pos1: Tuple[int, int] = self._zone_screen_pos(z1)
            pos2: Tuple[int, int] = self._zone_screen_pos(z2)
            pygame.draw.line(
                self.screen, (100, 100, 100), pos1, pos2, 2
            )

    def draw_zones(self) -> None:
        """Draw all zone circles with type-based coloring."""
        for zone in self.zones.values():
            # Base color from zone type
            if zone.zone_type == "blocked":
                base_color: Tuple[int, int, int] = (60, 60, 60)
            elif zone.zone_type == "restricted":
                base_color = (180, 60, 60)
            elif zone.zone_type == "priority":
                base_color = (60, 180, 60)
            elif zone.name == self.start_name:
                base_color = (50, 200, 50)
            elif zone.name == self.end_name:
                base_color = (200, 200, 50)
            else:
                base_color = (80, 120, 180)

            # Use map color if valid
            if zone.color and zone.color in self.colors:
                base_color = self.colors[zone.color]

            px, py = self._zone_screen_pos(zone)
            pygame.draw.circle(
                self.screen, base_color, (px, py), self.zone_radius
            )
            # Border
            pygame.draw.circle(
                self.screen, (200, 200, 200), (px, py),
                self.zone_radius, width=2
            )

    def draw_tooltip(self) -> None:
        """Draw a tooltip with zone info for the selected zone."""
        if self.selected_zone is None:
            return
        zone: Zone = self.selected_zone
        px, py = self._zone_screen_pos(zone)

        label: str = f"{zone.name}"
        details: str = f"type={zone.zone_type}  cap={zone.max_drones}"
        # Count drones currently here
        drones_here: int = sum(
            1 for did, zn in self.drone_positions.items()
            if zn == zone.name and did not in self.delivered
        )
        occupancy: str = f"drones: {drones_here}/{zone.max_drones}"

        img_name: pygame.Surface = self.font_large.render(
            label, True, (255, 255, 255)
        )
        img_details: pygame.Surface = self.font_hud.render(
            details, True, (200, 200, 200)
        )
        img_occ: pygame.Surface = self.font_hud.render(
            occupancy, True, (200, 200, 200)
        )
        line_h: int = img_name.get_height() + 4
        box_w: int = (
            max(
                img_name.get_width(),
                img_details.get_width(),
                img_occ.get_width(),
            )
            + 16
        )
        box_h: int = line_h * 3 + 16

        tx: int = px - box_w // 2
        ty: int = py - self.zone_radius - box_h - 6
        tx = max(4, min(tx, int(self.width) - box_w - 4))
        ty = max(4, ty)

        bg_rect: pygame.Rect = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(
            self.screen, (40, 40, 40), bg_rect, border_radius=6
        )
        pygame.draw.rect(
            self.screen, (255, 255, 255), bg_rect,
            width=1, border_radius=6
        )
        pygame.draw.circle(
            self.screen, (255, 255, 255), (px, py),
            self.zone_radius + 3, width=2
        )
        self.screen.blit(img_name, (tx + 8, ty + 6))
        self.screen.blit(img_details, (tx + 8, ty + 6 + line_h))
        self.screen.blit(img_occ, (tx + 8, ty + 6 + line_h * 2))

    def _get_drone_screen_pos(
        self, did: int
    ) -> Optional[Tuple[int, int]]:
        """Get the interpolated screen position for a drone.

        During animation, smoothly interpolates between previous and
        current zone positions. Otherwise returns the current zone pos.

        Args:
            did: Drone ID.

        Returns:
            (x, y) pixel position, or None if drone not found.
        """
        if did in self.delivered:
            return None

        # Check if drone is in transit on a connection
        if did in self.drone_transit:
            z_from, z_to = self.drone_transit[did]
            zone_from: Optional[Zone] = self.zone_map.get(z_from)
            zone_to: Optional[Zone] = self.zone_map.get(z_to)
            if zone_from and zone_to:
                p1: Tuple[int, int] = self._zone_screen_pos(zone_from)
                p2: Tuple[int, int] = self._zone_screen_pos(zone_to)
                t: float = min(self.anim_progress, 1.0) if self.animating else 0.5
                mx: int = int(p1[0] + (p2[0] - p1[0]) * 0.5 * (1.0 + t))
                my: int = int(p1[1] + (p2[1] - p1[1]) * 0.5 * (1.0 + t))
                return (mx, my)
            return None

        current_zone: str = self.drone_positions.get(did, self.start_name)
        prev_zone: str = self.drone_prev_positions.get(did, current_zone)

        zone_cur: Optional[Zone] = self.zone_map.get(current_zone)
        zone_prev: Optional[Zone] = self.zone_map.get(prev_zone)

        if not zone_cur:
            return None

        cur_pos: Tuple[int, int] = self._zone_screen_pos(zone_cur)

        # If animating and the drone moved this turn, interpolate
        if (
            self.animating
            and zone_prev
            and prev_zone != current_zone
        ):
            prev_pos: Tuple[int, int] = self._zone_screen_pos(zone_prev)
            t = self._ease_in_out(min(self.anim_progress, 1.0))
            ix: int = int(prev_pos[0] + (cur_pos[0] - prev_pos[0]) * t)
            iy: int = int(prev_pos[1] + (cur_pos[1] - prev_pos[1]) * t)
            return (ix, iy)

        return cur_pos

    @staticmethod
    def _ease_in_out(t: float) -> float:
        """Smooth ease-in-out interpolation.

        Args:
            t: Linear progress from 0.0 to 1.0.

        Returns:
            Eased progress value.
        """
        if t < 0.5:
            return 2.0 * t * t
        return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0

    def draw_drones(self) -> None:
        """Draw drones with smooth animated positions.

        Drones are drawn as colored circles with ID labels.
        Multiple drones at the same zone are spread around the center.
        """
        drone_r: int = max(8, self.zone_radius // 3)

        # Collect screen positions for all active drones
        drone_screen: List[Tuple[int, int, int]] = []  # (did, x, y)
        for did in self.drone_positions:
            pos: Optional[Tuple[int, int]] = self._get_drone_screen_pos(did)
            if pos:
                drone_screen.append((did, pos[0], pos[1]))

        # Group by position for spreading
        pos_groups: Dict[Tuple[int, int], List[int]] = {}
        for did, x, y in drone_screen:
            key: Tuple[int, int] = (x, y)
            if key not in pos_groups:
                pos_groups[key] = []
            pos_groups[key].append(did)

        for (bx, by), dids in pos_groups.items():
            n: int = len(dids)
            for i, did in enumerate(sorted(dids)):
                if n == 1:
                    dx, dy = 0, 0
                else:
                    angle: float = 2 * math.pi * i / n - math.pi / 2
                    spread: float = drone_r * 1.5
                    dx = int(spread * math.cos(angle))
                    dy = int(spread * math.sin(angle))
                color: Tuple[int, int, int] = self._drone_color(did)
                fx: int = bx + dx
                fy: int = by + dy
                # Glow effect
                glow: pygame.Surface = pygame.Surface(
                    (drone_r * 4, drone_r * 4), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    glow, (*color, 60),
                    (drone_r * 2, drone_r * 2), drone_r * 2
                )
                self.screen.blit(
                    glow, (fx - drone_r * 2, fy - drone_r * 2)
                )
                # Drone circle
                pygame.draw.circle(self.screen, color, (fx, fy), drone_r)
                pygame.draw.circle(
                    self.screen, (255, 255, 255),
                    (fx, fy), drone_r, width=2
                )
                # Label
                lbl: pygame.Surface = self.font.render(
                    f"D{did}", True, (255, 255, 255)
                )
                self.screen.blit(
                    lbl,
                    (fx - lbl.get_width() // 2, fy - drone_r - 16),
                )

    def draw_hud(self) -> None:
        """Draw the HUD overlay with turn counter and controls."""
        total: int = len(self.all_turns)
        turn_text: str = f"Turn: {self.current_turn}/{total}"
        status: str = (
            "DONE" if self.simulation_done
            else ("PAUSED" if self.paused else "PLAYING")
        )
        delivered_text: str = (
            f"Delivered: {len(self.delivered)}/{len(self.drones)}"
        )

        speed_pct: int = int(self.anim_speed * 100 / 0.15 * 100 / 100)
        # Top-left info panel
        panel_lines: List[str] = [
            turn_text,
            delivered_text,
            f"Status: {status}",
            f"Speed: {speed_pct}%",
            "",
            "SPACE: play/pause",
            "RIGHT: next  LEFT: prev",
            "R: reset  Q: quit",
            "+/-: speed",
        ]
        y_off: int = 10
        for line in panel_lines:
            if line:
                img: pygame.Surface = self.font_hud.render(
                    line, True, (220, 220, 220)
                )
                # Background for readability
                bg: pygame.Surface = pygame.Surface(
                    (img.get_width() + 8, img.get_height() + 4)
                )
                bg.set_alpha(160)
                bg.fill((20, 20, 20))
                self.screen.blit(bg, (8, y_off - 2))
                self.screen.blit(img, (12, y_off))
            y_off += 20

    def _apply_turn(self, turn_index: int) -> None:
        """Apply a single turn's moves to update drone positions.

        Saves previous positions for animation interpolation.

        Args:
            turn_index: The 0-based turn index.
        """
        if turn_index < 0 or turn_index >= len(self.all_turns):
            return

        # Save current positions as previous (for animation)
        self.drone_prev_positions = dict(self.drone_positions)

        moves: List[Tuple[int, str]] = self.all_turns[turn_index]
        self.anim_moves = moves

        # Clear transit state for drones that arrive this turn
        arrived: List[int] = []
        for did in list(self.drone_transit.keys()):
            if did in self.drone_transit:
                _, dest = self.drone_transit[did]
                self.drone_prev_positions[did] = self.drone_positions.get(
                    did, self.start_name
                )
                self.drone_positions[did] = dest
                arrived.append(did)
        for did in arrived:
            del self.drone_transit[did]

        for did, dest in moves:
            if "-" in dest and dest not in self.zone_map:
                # Transit move (connection toward restricted zone)
                parts: List[str] = dest.split("-", 1)
                if len(parts) == 2:
                    self.drone_transit[did] = (parts[0], parts[1])
            else:
                self.drone_positions[did] = dest
                if did in self.drone_transit:
                    del self.drone_transit[did]
                if dest == self.end_name:
                    self.delivered.add(did)

        if len(self.delivered) >= len(self.drones):
            self.simulation_done = True

        # Start animation
        self.animating = True
        self.anim_progress = 0.0

    def _reset_simulation(self) -> None:
        """Reset the simulation to turn 0."""
        self.current_turn = 0
        self.delivered = set()
        self.drone_transit = {}
        self.simulation_done = False
        self.animating = False
        self.anim_progress = 0.0
        self.anim_moves = []
        for drone in self.drones:
            self.drone_positions[drone.id] = self.start_name
            self.drone_prev_positions[drone.id] = self.start_name

    def _go_to_turn(self, target_turn: int) -> None:
        """Replay the simulation up to a specific turn.

        Args:
            target_turn: The turn to go to (1-based).
        """
        self._reset_simulation()
        for t in range(min(target_turn, len(self.all_turns))):
            self._apply_turn(t)
        self.current_turn = min(target_turn, len(self.all_turns))

    def run_simulation(
        self,
        all_turns: List[List[Tuple[int, str]]],
        drone_paths: List[List[str]],
    ) -> None:
        """Run the interactive simulation visualization.

        Args:
            all_turns: List of turns from the scheduler.
            drone_paths: List of assigned paths per drone.
        """
        self.all_turns = all_turns

        # Initialize drone positions
        for drone in self.drones:
            self.drone_positions[drone.id] = self.start_name

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        clicked: Optional[Zone] = self._get_zone_at(
                            *event.pos
                        )
                        if clicked == self.selected_zone:
                            self.selected_zone = None
                        else:
                            self.selected_zone = clicked

            # Update animation
            if self.animating:
                self.anim_progress += self.anim_speed
                if self.anim_progress >= 1.0:
                    self.anim_progress = 1.0
                    self.animating = False

            # Auto-play: advance to next turn when animation finishes
            if not self.paused and not self.simulation_done:
                if not self.animating:
                    self.auto_timer += 1
                    if self.auto_timer >= 20:  # brief pause between turns
                        self.auto_timer = 0
                        self._step_forward()

            # Draw everything
            self.screen.fill((30, 30, 30))
            self.draw_connections()
            self.draw_zones()
            self.draw_drones()
            self.draw_tooltip()
            self.draw_hud()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def _handle_key(self, key: int) -> None:
        """Handle keyboard input.

        Args:
            key: The pygame key constant.
        """
        if key == pygame.K_q:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_RIGHT:
            self._step_forward()
        elif key == pygame.K_LEFT:
            self._step_backward()
        elif key == pygame.K_r:
            self._reset_simulation()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.anim_speed = min(0.15, self.anim_speed + 0.01)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.anim_speed = max(0.005, self.anim_speed - 0.01)

    def _step_forward(self) -> None:
        """Advance the simulation by one turn."""
        if self.current_turn < len(self.all_turns):
            self._apply_turn(self.current_turn)
            self.current_turn += 1

    def _step_backward(self) -> None:
        """Go back one turn by replaying from the start."""
        if self.current_turn > 0:
            self._go_to_turn(self.current_turn - 1)