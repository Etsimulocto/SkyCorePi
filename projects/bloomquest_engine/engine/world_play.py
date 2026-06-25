# world_play.py
# run with: imported by editor/bloomquest_app.py
# path: projects/bloomquest_engine/engine/world_play.py
# description: Multi-room BloomQuest play-test runtime with movement, collision, counters, dialogue, collectibles, and doors.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, playtest, rooms, doors, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Loads room copies through RoomManager so editor files are never changed during testing.
# uuid: bc-bloomquest-worldplay-0001

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pygame

from engine.room_manager import RoomManager

LAYER_ORDER = ["map", "scene_objects", "actors", "weapons_effects"]


class WorldPlay:
    def __init__(self, room_manager: RoomManager, start_room_id: str, tile_size: int, canvas_rect: pygame.Rect) -> None:
        self.room_manager = room_manager
        self.tile_size = tile_size
        self.canvas_rect = canvas_rect
        self.room_id = start_room_id
        self.room = deepcopy(room_manager.load(start_room_id))
        self.session_rooms: dict[str, dict[str, Any]] = {start_room_id: self.room}
        self.counters = deepcopy(self.room.get("counters", {}))
        for key, value in {"health": 3, "coins": 0, "score": 0, "keys": 0}.items():
            self.counters.setdefault(key, value)
        self.player_x, self.player_y, self.player_emoji = self.find_spawn()
        self.camera_x = 0
        self.camera_y = 0
        self.message = ""
        self.status = "WASD / Arrows move | E interact | Esc return"
        self.center_camera()

    def find_spawn(self) -> tuple[int, int, str]:
        for item in self.room.get("layers", {}).get("actors", []):
            if item.get("part_id") == "player":
                return int(item.get("x", 1)), int(item.get("y", 1)), item.get("emoji", "🧍")
        return 1, 1, "🧍"

    def handle_key(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_ESCAPE:
            return False
        movement = {
            pygame.K_w: (0, -1), pygame.K_UP: (0, -1),
            pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
            pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
            pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
        }
        if event.key in movement:
            self.try_move(*movement[event.key])
        elif event.key == pygame.K_e:
            self.interact()
        return True

    def try_move(self, dx: int, dy: int) -> None:
        nx, ny = self.player_x + dx, self.player_y + dy
        grid = self.room.get("grid", {})
        if not (0 <= nx < int(grid.get("columns", 128)) and 0 <= ny < int(grid.get("rows", 128))):
            return
        if any(item.get("solid", False) and item.get("part_id") != "player" for item in self.items_at(nx, ny)):
            self.status = "Blocked."
            return
        self.player_x, self.player_y = nx, ny
        for item in list(self.items_at(nx, ny)):
            action = item.get("action", {})
            if action.get("trigger") == "player_touch":
                self.execute(item, action)
        self.center_camera()

    def items_at(self, x: int, y: int) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for layer in LAYER_ORDER:
            for item in self.room.get("layers", {}).get(layer, []):
                if item.get("enabled", True) and item.get("x") == x and item.get("y") == y:
                    found.append(item)
        return found

    def interact(self) -> None:
        for dx, dy in ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)):
            for item in self.items_at(self.player_x + dx, self.player_y + dy):
                action = item.get("action", {})
                if action.get("trigger") == "player_use":
                    self.execute(item, action)
                    return
        self.status = "Nothing to interact with."

    def execute(self, item: dict[str, Any], action: dict[str, Any]) -> None:
        kind = action.get("type", "none")
        if kind == "show_text":
            self.message = action.get("text") or item.get("description", "")
            self.status = item.get("name", "Message")
        elif kind == "add_counter":
            name = action.get("counter") or "score"
            amount = int(action.get("amount", 1))
            self.counters[name] = int(self.counters.get(name, 0)) + amount
            self.status = f"{name} {amount:+d}"
        elif kind == "heal_player":
            amount = int(action.get("amount", 1))
            self.counters["health"] = int(self.counters.get("health", 0)) + amount
        elif kind == "damage_player":
            amount = int(action.get("amount", item.get("damage", 1)))
            self.counters["health"] = max(0, int(self.counters.get("health", 0)) - amount)
        elif kind == "teleport":
            target_room = action.get("target_room") or self.room_id
            target_x = int(action.get("target_x", 1))
            target_y = int(action.get("target_y", 1))
            self.change_room(target_room, target_x, target_y)
        if action.get("destroy_self"):
            self.remove_item(item)

    def change_room(self, room_id: str, x: int, y: int) -> None:
        try:
            if room_id not in self.session_rooms:
                self.session_rooms[room_id] = deepcopy(self.room_manager.load(room_id))
            self.room_id = room_id
            self.room = self.session_rooms[room_id]
            self.player_x, self.player_y = x, y
            self.message = ""
            self.status = f"Entered {self.room.get('name', room_id)}"
            self.center_camera()
        except Exception:
            self.message = f"Room not found: {room_id}"
            self.status = "Door failed."

    def remove_item(self, target: dict[str, Any]) -> None:
        for layer in LAYER_ORDER:
            items = self.room.get("layers", {}).get(layer, [])
            if target in items:
                items.remove(target)
                return

    def center_camera(self) -> None:
        grid = self.room.get("grid", {})
        world_w = int(grid.get("columns", 128)) * self.tile_size
        world_h = int(grid.get("rows", 128)) * self.tile_size
        self.camera_x = max(0, min(max(0, world_w - self.canvas_rect.width), self.player_x * self.tile_size - self.canvas_rect.width // 2))
        self.camera_y = max(0, min(max(0, world_h - self.canvas_rect.height), self.player_y * self.tile_size - self.canvas_rect.height // 2))

    def draw(self, surface: pygame.Surface, draw_item: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None], colors: dict[str, tuple[int, int, int]], fonts: dict[str, pygame.font.Font]) -> None:
        pygame.draw.rect(surface, colors["canvas"], self.canvas_rect)
        surface.set_clip(self.canvas_rect)
        start_x = self.camera_x // self.tile_size
        start_y = self.camera_y // self.tile_size
        for gy in range(start_y, start_y + self.canvas_rect.height // self.tile_size + 2):
            for gx in range(start_x, start_x + self.canvas_rect.width // self.tile_size + 2):
                sx = self.canvas_rect.x + gx * self.tile_size - self.camera_x
                sy = self.canvas_rect.y + gy * self.tile_size - self.camera_y
                pygame.draw.rect(surface, colors["grid"], (sx, sy, self.tile_size, self.tile_size), 1)
        for layer in LAYER_ORDER:
            for item in self.room.get("layers", {}).get(layer, []):
                if item.get("part_id") != "player":
                    draw_item(surface, item, self.camera_x, self.camera_y, False)
        draw_item(surface, {"x": self.player_x, "y": self.player_y, "emoji": self.player_emoji, "color": [235, 235, 235]}, self.camera_x, self.camera_y, False)
        surface.set_clip(None)

        hud = pygame.Rect(self.canvas_rect.x + 10, self.canvas_rect.y + 10, 500, 38)
        pygame.draw.rect(surface, colors["panel"], hud, border_radius=7)
        label = f"{self.room_id}   ❤️ {self.counters.get('health', 0)}   🪙 {self.counters.get('coins', 0)}   ⭐ {self.counters.get('score', 0)}   🗝️ {self.counters.get('keys', 0)}"
        image = fonts["medium"].render(label, True, colors["text"])
        surface.blit(image, image.get_rect(midleft=(hud.x + 12, hud.centery)))

        if self.message:
            box = pygame.Rect(self.canvas_rect.x + 40, self.canvas_rect.bottom - 110, self.canvas_rect.width - 80, 72)
            pygame.draw.rect(surface, colors["panel"], box, border_radius=8)
            pygame.draw.rect(surface, colors["accent"], box, 2, border_radius=8)
            image = fonts["medium"].render(self.message[:90], True, colors["text"])
            surface.blit(image, (box.x + 14, box.y + 22))
