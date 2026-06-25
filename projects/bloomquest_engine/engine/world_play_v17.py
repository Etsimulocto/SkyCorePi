# world_play_v17.py
# run with: imported by editor/bloomquest_app_v17.py
# path: projects/bloomquest_engine/engine/world_play_v17.py
# description: Adds room-wide color overlays, fog, grain, vignette, cave darkness, and dynamic light sources.
# version: 0.17.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, overlay, darkness, fog, vignette, lighting, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Dynamic lights include player, torches, runes, projectiles, bombs, and explosions.
# uuid: bc-bloomquest-worldplay-0017

from __future__ import annotations

import math
import random
from typing import Any, Callable

import pygame

from engine.world_play_v16 import WorldPlayV16


OVERLAY_PRESETS = {
    "none": ((0, 0, 0), 0),
    "night": ((20, 35, 85), 105),
    "cave": ((4, 7, 12), 215),
    "fog": ((165, 175, 185), 70),
    "dust": ((125, 95, 55), 45),
    "underwater": ((20, 95, 150), 90),
    "heat": ((200, 75, 20), 48),
    "poison": ((60, 135, 45), 75),
    "dream": ((100, 45, 155), 75),
    "old_film": ((105, 85, 55), 72),
    "storm": ((25, 35, 60), 125),
    "custom": ((30, 30, 30), 100),
}


class WorldPlayV17(WorldPlayV16):
    """Complete game loop with cinematic overlays and dynamic lighting."""

    def __init__(self, *args, overlay_config: dict[str, Any] | None = None, **kwargs) -> None:
        self.overlay_config = dict(overlay_config or {})
        super().__init__(*args, **kwargs)
        self.overlay_particles = self.make_overlay_particles()
        self.last_lightning_ms = 0
        self.lightning_until_ms = 0

    def overlay_value(self, key: str, default: Any) -> Any:
        return self.overlay_config.get(key, default)

    def make_overlay_particles(self) -> list[dict[str, float]]:
        rng = random.Random(825 + sum(ord(c) for c in self.room_id))
        return [
            {
                "x": rng.uniform(0, self.canvas_rect.width),
                "y": rng.uniform(0, self.canvas_rect.height),
                "speed": rng.uniform(0.15, 0.8),
                "size": rng.uniform(1.0, 4.0),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(70)
        ]

    def update(self) -> None:
        super().update()
        if self.state != "playing":
            return

        now = pygame.time.get_ticks()
        if self.overlay_value("type", "none") == "storm":
            interval = max(1500, int(self.overlay_value("lightning_interval_ms", 4500)))
            if now - self.last_lightning_ms >= interval:
                self.last_lightning_ms = now
                self.lightning_until_ms = now + 120

    def draw(
        self,
        surface: pygame.Surface,
        draw_item: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None],
        colors: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        super().draw(surface, draw_item, colors, fonts)
        if self.state == "playing" and not self.game_over:
            self.draw_room_overlay(surface)

    def draw_room_overlay(self, surface: pygame.Surface) -> None:
        overlay_type = str(self.overlay_value("type", "none"))
        if overlay_type == "none":
            return

        preset_color, preset_alpha = OVERLAY_PRESETS.get(overlay_type, OVERLAY_PRESETS["custom"])
        color = tuple(self.overlay_value("color", preset_color))
        alpha = max(0, min(255, int(self.overlay_value("opacity", preset_alpha))))
        texture_strength = max(0, min(100, int(self.overlay_value("texture_strength", 30))))
        vignette_strength = max(0, min(100, int(self.overlay_value("vignette", 25))))

        layer = pygame.Surface(self.canvas_rect.size, pygame.SRCALPHA)
        layer.fill((*color, alpha))

        if overlay_type == "cave":
            self.punch_dynamic_lights(layer)
        elif overlay_type in ("fog", "dust", "old_film", "dream"):
            self.draw_texture(layer, overlay_type, texture_strength)
        elif overlay_type == "underwater":
            self.draw_underwater_bands(layer)
        elif overlay_type == "heat":
            self.draw_heat_shimmer(layer)
        elif overlay_type == "storm":
            self.draw_storm_texture(layer, texture_strength)

        surface.blit(layer, self.canvas_rect.topleft)

        if vignette_strength:
            self.draw_vignette(surface, vignette_strength)

        if overlay_type == "storm" and pygame.time.get_ticks() < self.lightning_until_ms:
            flash = pygame.Surface(self.canvas_rect.size, pygame.SRCALPHA)
            flash.fill((220, 230, 255, 120))
            surface.blit(flash, self.canvas_rect.topleft)

    def punch_dynamic_lights(self, layer: pygame.Surface) -> None:
        player_radius = max(1, int(self.overlay_value("player_light_radius", 5))) * self.tile_size
        softness = max(1, int(self.overlay_value("light_softness", 70)))
        self.punch_soft_light(layer, self.player_screen_position(), player_radius, softness)

        for item in self.room.get("layers", {}).get("decorations", []):
            part_id = item.get("part_id")
            if part_id in ("torch", "rune"):
                radius_tiles = 3 if part_id == "torch" else 2
                self.punch_soft_light(layer, self.item_screen_position(item), radius_tiles * self.tile_size, softness)

        for shot in getattr(self, "projectiles", []):
            self.punch_soft_light(layer, self.item_screen_position(shot), 2 * self.tile_size, softness)

        for bomb in getattr(self, "bombs", []):
            self.punch_soft_light(layer, self.item_screen_position(bomb), 2 * self.tile_size, softness)

        for effect in getattr(self, "effects", []):
            self.punch_soft_light(layer, self.item_screen_position(effect), 3 * self.tile_size, softness)

    def player_screen_position(self) -> tuple[int, int]:
        return (
            self.player_x * self.tile_size - self.camera_x + self.tile_size // 2,
            self.player_y * self.tile_size - self.camera_y + self.tile_size // 2,
        )

    def item_screen_position(self, item: dict[str, Any]) -> tuple[int, int]:
        return (
            int(item.get("x", 0)) * self.tile_size - self.camera_x + self.tile_size // 2,
            int(item.get("y", 0)) * self.tile_size - self.camera_y + self.tile_size // 2,
        )

    @staticmethod
    def punch_soft_light(layer: pygame.Surface, center: tuple[int, int], radius: int, softness: int) -> None:
        steps = max(4, min(18, softness // 6))
        for index in range(steps, 0, -1):
            fraction = index / steps
            current_radius = max(1, int(radius * fraction))
            alpha = int(220 * (1.0 - fraction) ** 1.7)
            pygame.draw.circle(layer, (0, 0, 0, alpha), center, current_radius)
        pygame.draw.circle(layer, (0, 0, 0, 0), center, max(1, radius // 3))

    def draw_texture(self, layer: pygame.Surface, overlay_type: str, strength: int) -> None:
        now = pygame.time.get_ticks()
        for particle in self.overlay_particles:
            x = int((particle["x"] + now * particle["speed"] * 0.02) % self.canvas_rect.width)
            y = int((particle["y"] + math.sin(now / 700 + particle["phase"]) * 18) % self.canvas_rect.height)
            size = max(1, int(particle["size"] + strength / 35))
            if overlay_type == "fog":
                pygame.draw.circle(layer, (225, 230, 235, 12 + strength // 4), (x, y), size * 5)
            elif overlay_type == "dust":
                pygame.draw.circle(layer, (220, 180, 110, 20 + strength // 3), (x, y), size)
            elif overlay_type == "dream":
                pygame.draw.circle(layer, (210, 160, 255, 18 + strength // 3), (x, y), size * 2)
            else:
                pygame.draw.circle(layer, (255, 245, 210, 18 + strength // 4), (x, y), 1)

        if overlay_type == "old_film":
            rng = random.Random(now // 90)
            for _ in range(4 + strength // 12):
                x = rng.randrange(0, max(1, self.canvas_rect.width))
                pygame.draw.line(layer, (245, 235, 205, 25), (x, 0), (x, self.canvas_rect.height), 1)

    def draw_underwater_bands(self, layer: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        for y in range(0, self.canvas_rect.height, 48):
            offset = int(math.sin(now / 420 + y / 70) * 18)
            pygame.draw.line(layer, (120, 210, 240, 30), (offset, y), (self.canvas_rect.width + offset, y), 3)

    def draw_heat_shimmer(self, layer: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        for y in range(0, self.canvas_rect.height, 36):
            offset = int(math.sin(now / 250 + y / 40) * 12)
            pygame.draw.line(layer, (255, 190, 90, 25), (offset, y), (self.canvas_rect.width + offset, y), 2)

    def draw_storm_texture(self, layer: pygame.Surface, strength: int) -> None:
        now = pygame.time.get_ticks()
        for particle in self.overlay_particles[: 20 + strength // 4]:
            x = int((particle["x"] + now * 0.22) % self.canvas_rect.width)
            y = int((particle["y"] + now * 0.35) % self.canvas_rect.height)
            pygame.draw.line(layer, (140, 180, 230, 60), (x, y), (x - 5, y + 12), 1)

    def draw_vignette(self, surface: pygame.Surface, strength: int) -> None:
        vignette = pygame.Surface(self.canvas_rect.size, pygame.SRCALPHA)
        max_alpha = int(180 * strength / 100)
        steps = 20
        for index in range(steps):
            inset = index * min(self.canvas_rect.width, self.canvas_rect.height) // (steps * 5)
            alpha = int(max_alpha * (1.0 - index / steps) ** 1.8)
            rect = pygame.Rect(inset, inset, self.canvas_rect.width - inset * 2, self.canvas_rect.height - inset * 2)
            if rect.width > 0 and rect.height > 0:
                pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, max(2, inset // 2 + 2), border_radius=18)
        surface.blit(vignette, self.canvas_rect.topleft)
