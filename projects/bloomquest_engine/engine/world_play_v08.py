# world_play_v08.py
# run with: imported by editor/bloomquest_app_v08.py
# path: projects/bloomquest_engine/engine/world_play_v08.py
# description: Adds equipped orbiting weapons and enemy damage to the multi-room play runtime.
# version: 0.8.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, sword, orbit, combat, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: A placed Sword equips the player; it is never collected as a pickup.
# uuid: bc-bloomquest-worldplay-0008

from __future__ import annotations

import math
from typing import Any, Callable

import pygame

from engine.world_play import WorldPlay

LAYER_ORDER_V08 = ["map", "scene_objects", "actors", "weapons", "weapons_effects"]


class WorldPlayV08(WorldPlay):
    """World runtime with automatically orbiting equipped weapons."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.weapon_angle = 0.0
        self.last_update_ms = pygame.time.get_ticks()
        self.last_hit_step = -1
        self.weapon_font = pygame.font.SysFont("Segoe UI Emoji", 25)
        self.status = "Move: WASD / D-pad | Interact: E / A | Sword orbits automatically"

    def items_at(self, x: int, y: int) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for layer in LAYER_ORDER_V08:
            for item in self.room.get("layers", {}).get(layer, []):
                if item.get("enabled", True) and item.get("x") == x and item.get("y") == y:
                    found.append(item)
        return found

    def equipped_sword(self) -> dict[str, Any] | None:
        """Return the first placed sword in either new or legacy weapon layers."""
        for layer in ("weapons", "weapons_effects"):
            for item in self.room.get("layers", {}).get(layer, []):
                if item.get("part_id") == "sword" and item.get("enabled", True):
                    return item
        return None

    def update(self) -> None:
        sword = self.equipped_sword()
        if sword is None:
            return

        now = pygame.time.get_ticks()
        elapsed = max(0, now - self.last_update_ms)
        self.last_update_ms = now

        speed_ms = int(sword.get("weapon", {}).get("speed_ms", 120))
        radians_per_ms = (math.tau / 8.0) / max(1, speed_ms)
        self.weapon_angle = (self.weapon_angle + elapsed * radians_per_ms) % math.tau

        step = int((self.weapon_angle / math.tau) * 8) % 8
        if step != self.last_hit_step:
            self.last_hit_step = step
            self.damage_enemy_at_weapon(step, sword)

    def weapon_grid_offset(self, step: int) -> tuple[int, int]:
        offsets = [
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
            (0, -1),
            (1, -1),
        ]
        return offsets[step % len(offsets)]

    def damage_enemy_at_weapon(self, step: int, sword: dict[str, Any]) -> None:
        dx, dy = self.weapon_grid_offset(step)
        target_x = self.player_x + dx
        target_y = self.player_y + dy
        damage = max(1, int(sword.get("damage", 1)))

        for enemy in list(self.room.get("layers", {}).get("actors", [])):
            if enemy.get("part_id") in ("player", "villager"):
                continue
            if enemy.get("x") != target_x or enemy.get("y") != target_y:
                continue
            if "health" not in enemy:
                continue

            enemy["health"] = int(enemy.get("health", 1)) - damage
            self.status = f"Sword hit {enemy.get('name', 'enemy')} for {damage}"

            if enemy["health"] <= 0:
                self.room["layers"]["actors"].remove(enemy)
                self.counters["score"] = int(self.counters.get("score", 0)) + 1
                self.status = f"Defeated {enemy.get('name', 'enemy')}!"
            break

    def draw(
        self,
        surface: pygame.Surface,
        draw_item: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None],
        colors: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        pygame.draw.rect(surface, colors["canvas"], self.canvas_rect)
        surface.set_clip(self.canvas_rect)

        start_x = self.camera_x // self.tile_size
        start_y = self.camera_y // self.tile_size
        for gy in range(start_y, start_y + self.canvas_rect.height // self.tile_size + 2):
            for gx in range(start_x, start_x + self.canvas_rect.width // self.tile_size + 2):
                sx = self.canvas_rect.x + gx * self.tile_size - self.camera_x
                sy = self.canvas_rect.y + gy * self.tile_size - self.camera_y
                pygame.draw.rect(surface, colors["grid"], (sx, sy, self.tile_size, self.tile_size), 1)

        for layer in LAYER_ORDER_V08:
            for item in self.room.get("layers", {}).get(layer, []):
                if item.get("part_id") in ("player", "sword"):
                    continue
                draw_item(surface, item, self.camera_x, self.camera_y, False)

        player_item = {
            "x": self.player_x,
            "y": self.player_y,
            "emoji": self.player_emoji,
            "color": [235, 235, 235],
        }
        draw_item(surface, player_item, self.camera_x, self.camera_y, False)

        sword = self.equipped_sword()
        if sword is not None:
            player_center_x = self.canvas_rect.x + self.player_x * self.tile_size - self.camera_x + self.tile_size // 2
            player_center_y = self.canvas_rect.y + self.player_y * self.tile_size - self.camera_y + self.tile_size // 2
            radius = self.tile_size * float(sword.get("weapon", {}).get("radius", 1.0))
            sword_x = player_center_x + math.cos(self.weapon_angle) * radius
            sword_y = player_center_y + math.sin(self.weapon_angle) * radius
            sword_image = self.weapon_font.render(sword.get("emoji", "🗡️"), True, colors["text"])
            sword_rect = sword_image.get_rect(center=(round(sword_x), round(sword_y)))
            surface.blit(sword_image, sword_rect)

        surface.set_clip(None)

        hud = pygame.Rect(self.canvas_rect.x + 10, self.canvas_rect.y + 10, 560, 38)
        pygame.draw.rect(surface, colors["panel"], hud, border_radius=7)
        weapon_text = "🗡️ Equipped" if sword is not None else "No weapon"
        label = (
            f"{self.room_id}   ❤️ {self.counters.get('health', 0)}   "
            f"🪙 {self.counters.get('coins', 0)}   ⭐ {self.counters.get('score', 0)}   "
            f"🗝️ {self.counters.get('keys', 0)}   {weapon_text}"
        )
        image = fonts["medium"].render(label, True, colors["text"])
        surface.blit(image, image.get_rect(midleft=(hud.x + 12, hud.centery)))

        if self.message:
            box = pygame.Rect(self.canvas_rect.x + 40, self.canvas_rect.bottom - 110, self.canvas_rect.width - 80, 72)
            pygame.draw.rect(surface, colors["panel"], box, border_radius=8)
            pygame.draw.rect(surface, colors["accent"], box, 2, border_radius=8)
            image = fonts["medium"].render(self.message[:90], True, colors["text"])
            surface.blit(image, (box.x + 14, box.y + 22))
