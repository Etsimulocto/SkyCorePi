# play_mode.py
# run with: imported by main.py
# path: projects/bloomquest_engine/engine/play_mode.py
# description: BloomQuest play-test runtime with movement, collision, counters, collectibles, dialogue, and door checks.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, pygame, playtest, runtime, collision, counters
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Runtime edits a deep copy of the room so play-testing never damages editor data.
# uuid: bc-bloomquest-playmode-0001

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pygame


LAYER_ORDER = ["map", "scene_objects", "actors", "weapons_effects"]


class PlayMode:
    """Grid-based play-test runtime for one BloomQuest room."""

    def __init__(
        self,
        room: dict[str, Any],
        tile_size: int,
        canvas_rect: pygame.Rect,
        font_small: pygame.font.Font,
        font_medium: pygame.font.Font,
        font_emoji: pygame.font.Font,
        colors: dict[str, tuple[int, int, int]],
    ) -> None:
        self.room = deepcopy(room)
        self.tile_size = tile_size
        self.canvas_rect = canvas_rect
        self.font_small = font_small
        self.font_medium = font_medium
        self.font_emoji = font_emoji
        self.colors = colors

        self.player = self.find_player()
        self.player_x = int(self.player.get("x", 1)) if self.player else 1
        self.player_y = int(self.player.get("y", 1)) if self.player else 1
        self.player_emoji = self.player.get("emoji", "🧍") if self.player else "🧍"

        self.counters = deepcopy(self.room.get("counters", {}))
        self.counters.setdefault("health", 3)
        self.counters.setdefault("coins", 0)
        self.counters.setdefault("score", 0)
        self.counters.setdefault("keys", 0)

        self.camera_x = max(0, self.player_x * tile_size - canvas_rect.width // 2)
        self.camera_y = max(0, self.player_y * tile_size - canvas_rect.height // 2)

        self.message = ""
        self.message_timer = 0
        self.status = "WASD / Arrows move | E interact | Esc return to editor"

    def find_player(self) -> dict[str, Any] | None:
        for instance in self.room.get("layers", {}).get("actors", []):
            if instance.get("part_id") == "player":
                return instance
        return None

    def handle_key(self, event: pygame.event.Event) -> bool:
        """Handle play-mode keys. Return False to exit play mode."""
        if event.key == pygame.K_ESCAPE:
            return False

        movement = {
            pygame.K_w: (0, -1),
            pygame.K_UP: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_DOWN: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_LEFT: (-1, 0),
            pygame.K_d: (1, 0),
            pygame.K_RIGHT: (1, 0),
        }

        if event.key in movement:
            delta_x, delta_y = movement[event.key]
            self.try_move(delta_x, delta_y)
        elif event.key == pygame.K_e:
            self.interact()

        return True

    def try_move(self, delta_x: int, delta_y: int) -> None:
        target_x = self.player_x + delta_x
        target_y = self.player_y + delta_y

        grid = self.room.get("grid", {})
        columns = int(grid.get("columns", 128))
        rows = int(grid.get("rows", 128))

        if not (0 <= target_x < columns and 0 <= target_y < rows):
            return

        if self.is_solid(target_x, target_y):
            self.status = "Blocked."
            return

        self.player_x = target_x
        self.player_y = target_y
        self.run_touch_actions()
        self.center_camera()

    def center_camera(self) -> None:
        grid = self.room.get("grid", {})
        world_width = int(grid.get("columns", 128)) * self.tile_size
        world_height = int(grid.get("rows", 128)) * self.tile_size

        self.camera_x = max(0, min(world_width - self.canvas_rect.width, self.player_x * self.tile_size - self.canvas_rect.width // 2))
        self.camera_y = max(0, min(world_height - self.canvas_rect.height, self.player_y * self.tile_size - self.canvas_rect.height // 2))

    def all_instances_at(self, grid_x: int, grid_y: int) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for layer_name in LAYER_ORDER:
            for instance in self.room.get("layers", {}).get(layer_name, []):
                if instance.get("enabled", True) and instance.get("x") == grid_x and instance.get("y") == grid_y:
                    found.append(instance)
        return found

    def is_solid(self, grid_x: int, grid_y: int) -> bool:
        for instance in self.all_instances_at(grid_x, grid_y):
            if instance.get("part_id") == "player":
                continue
            if instance.get("solid", False):
                return True
        return False

    def run_touch_actions(self) -> None:
        for instance in list(self.all_instances_at(self.player_x, self.player_y)):
            if instance.get("part_id") == "player":
                continue

            action = instance.get("action", {})
            if action.get("trigger") == "player_touch":
                self.execute_action(instance, action)

    def interact(self) -> None:
        candidates: list[dict[str, Any]] = []
        for offset_x, offset_y in ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)):
            candidates.extend(self.all_instances_at(self.player_x + offset_x, self.player_y + offset_y))

        for instance in candidates:
            if instance.get("part_id") == "player":
                continue
            action = instance.get("action", {})
            if action.get("trigger") == "player_use":
                self.execute_action(instance, action)
                return

        self.status = "Nothing to interact with."

    def execute_action(self, instance: dict[str, Any], action: dict[str, Any]) -> None:
        action_type = action.get("type", "none")

        if action_type == "add_counter":
            counter_name = action.get("counter", "score") or "score"
            amount = int(action.get("amount", 1))
            self.counters[counter_name] = int(self.counters.get(counter_name, 0)) + amount
            self.status = f"{counter_name} {amount:+d}"

        elif action_type == "show_text":
            self.message = action.get("text", instance.get("description", "")) or instance.get("description", "")
            self.message_timer = 360
            self.status = instance.get("name", "Message")

        elif action_type == "heal_player":
            amount = int(action.get("amount", 1))
            self.counters["health"] = int(self.counters.get("health", 0)) + amount
            self.status = f"Health +{amount}"

        elif action_type == "damage_player":
            amount = int(action.get("amount", instance.get("damage", 1)))
            self.counters["health"] = max(0, int(self.counters.get("health", 0)) - amount)
            self.status = f"Health -{amount}"

        elif action_type == "teleport":
            target_room = action.get("target_room", "")
            target_x = int(action.get("target_x", self.player_x))
            target_y = int(action.get("target_y", self.player_y))
            current_room = self.room.get("room_id", "room_001")

            if target_room and target_room != current_room:
                self.message = f"Door points to {target_room}. Multi-room loading comes next."
                self.message_timer = 360
                self.status = "Door target recorded."
            else:
                self.player_x = target_x
                self.player_y = target_y
                self.center_camera()
                self.status = f"Teleported to {target_x}, {target_y}"

        if action.get("destroy_self", False):
            self.remove_instance(instance)

    def remove_instance(self, target: dict[str, Any]) -> None:
        for layer_name in LAYER_ORDER:
            layer = self.room.get("layers", {}).get(layer_name, [])
            if target in layer:
                layer.remove(target)
                return

    def update(self) -> None:
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""

    def draw(
        self,
        surface: pygame.Surface,
        draw_instance: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None],
    ) -> None:
        surface.set_clip(self.canvas_rect)
        pygame.draw.rect(surface, self.colors["canvas"], self.canvas_rect)

        start_column = self.camera_x // self.tile_size
        start_row = self.camera_y // self.tile_size
        end_column = start_column + self.canvas_rect.width // self.tile_size + 2
        end_row = start_row + self.canvas_rect.height // self.tile_size + 2

        for grid_y in range(start_row, end_row):
            for grid_x in range(start_column, end_column):
                screen_x = self.canvas_rect.x + grid_x * self.tile_size - self.camera_x
                screen_y = self.canvas_rect.y + grid_y * self.tile_size - self.camera_y
                pygame.draw.rect(surface, self.colors["grid"], (screen_x, screen_y, self.tile_size, self.tile_size), width=1)

        for layer_name in LAYER_ORDER:
            for instance in self.room.get("layers", {}).get(layer_name, []):
                if instance.get("part_id") == "player":
                    continue
                draw_instance(surface, instance, self.camera_x, self.camera_y, False)

        player_instance = {
            "x": self.player_x,
            "y": self.player_y,
            "emoji": self.player_emoji,
            "color": [235, 235, 235],
        }
        draw_instance(surface, player_instance, self.camera_x, self.camera_y, False)

        surface.set_clip(None)
        pygame.draw.rect(surface, self.colors["grid"], self.canvas_rect, width=1)

        self.draw_hud(surface)

    def draw_hud(self, surface: pygame.Surface) -> None:
        hud_rect = pygame.Rect(self.canvas_rect.x + 10, self.canvas_rect.y + 10, 430, 38)
        pygame.draw.rect(surface, self.colors["panel"], hud_rect, border_radius=7)

        hud_text = (
            f"❤️ {self.counters.get('health', 0)}   "
            f"🪙 {self.counters.get('coins', 0)}   "
            f"⭐ {self.counters.get('score', 0)}   "
            f"🗝️ {self.counters.get('keys', 0)}"
        )
        hud_surface = self.font_medium.render(hud_text, True, self.colors["text"])
        surface.blit(hud_surface, hud_surface.get_rect(midleft=(hud_rect.x + 12, hud_rect.centery)))

        if self.message:
            message_rect = pygame.Rect(self.canvas_rect.x + 40, self.canvas_rect.bottom - 120, self.canvas_rect.width - 80, 82)
            pygame.draw.rect(surface, self.colors["panel"], message_rect, border_radius=8)
            pygame.draw.rect(surface, self.colors["accent"], message_rect, width=2, border_radius=8)

            words = self.message.split()
            lines: list[str] = []
            current = ""
            for word in words:
                test = word if not current else f"{current} {word}"
                if self.font_medium.size(test)[0] <= message_rect.width - 28:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)

            for index, line in enumerate(lines[:2]):
                text_surface = self.font_medium.render(line, True, self.colors["text"])
                surface.blit(text_surface, (message_rect.x + 14, message_rect.y + 13 + index * 28))
