# world_play_v13.py
# run with: imported by editor/bloomquest_app_v13.py
# description: Draws animated decorations and room-wide rain, snow, and firefly atmosphere effects.

from __future__ import annotations

import math
import random
from typing import Any

import pygame

from engine.world_play_v11 import WorldPlayV11


class WorldPlayV13(WorldPlayV11):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.decor_font = pygame.font.SysFont("Segoe UI Emoji", 23)
        self.particles = self.make_particles()

    def atmosphere_types(self) -> set[str]:
        return {
            str(item.get("atmosphere"))
            for item in self.room.get("layers", {}).get("decorations", [])
            if item.get("atmosphere")
        }

    def make_particles(self) -> list[dict[str, Any]]:
        particles: list[dict[str, Any]] = []
        for index in range(42):
            particles.append({
                "x": random.randint(0, max(1, self.canvas_rect.width - 1)),
                "y": random.randint(0, max(1, self.canvas_rect.height - 1)),
                "speed": random.randint(1, 4),
                "phase": index * 0.63,
            })
        return particles

    def change_room(self, room_id: str, x: int, y: int) -> None:
        super().change_room(room_id, x, y)
        self.particles = self.make_particles()

    def draw(self, surface, draw_item, colors, fonts) -> None:
        super().draw(surface, draw_item, colors, fonts)
        surface.set_clip(self.canvas_rect)
        now = pygame.time.get_ticks()

        for item in self.room.get("layers", {}).get("decorations", []):
            if item.get("hidden_in_play"):
                continue
            self.draw_decoration(surface, item, now, colors)

        self.draw_atmosphere(surface, now)
        surface.set_clip(None)

    def draw_decoration(self, surface: pygame.Surface, item: dict[str, Any], now: int, colors) -> None:
        animation = item.get("animation", {})
        kind = str(animation.get("type", "none"))
        speed = max(1, int(animation.get("speed_ms", 500)))
        amount = int(animation.get("amount", 2))
        phase = (now / speed) * math.tau
        offset_x = 0
        offset_y = 0

        if kind == "bob":
            offset_y = round(math.sin(phase) * amount)
        elif kind == "sway":
            offset_x = round(math.sin(phase) * amount)
        elif kind == "pulse":
            offset_y = round(math.sin(phase) * max(1, amount // 2))
        elif kind == "flicker":
            offset_x = -1 if int(now / speed) % 2 else 1

        sx = self.canvas_rect.x + int(item.get("x", 0)) * self.tile_size - self.camera_x
        sy = self.canvas_rect.y + int(item.get("y", 0)) * self.tile_size - self.camera_y
        emoji = str(item.get("emoji", ""))
        image = self.decor_font.render(emoji, True, colors["text"])
        surface.blit(image, image.get_rect(center=(sx + self.tile_size // 2 + offset_x, sy + self.tile_size // 2 + offset_y)))

    def draw_atmosphere(self, surface: pygame.Surface, now: int) -> None:
        active = self.atmosphere_types()
        if not active:
            return

        for index, particle in enumerate(self.particles):
            x = self.canvas_rect.x + int(particle["x"])
            y = self.canvas_rect.y + int(particle["y"])

            if "rain" in active:
                pygame.draw.line(surface, (120, 170, 225), (x, y), (x - 3, y + 8), 1)
            elif "snow" in active:
                pygame.draw.circle(surface, (235, 240, 250), (x, y), 2)
            elif "fireflies" in active:
                pulse = 1 + int((math.sin(now / 220 + particle["phase"]) + 1) / 2)
                pygame.draw.circle(surface, (245, 235, 100), (x, y), pulse)

            particle["y"] += particle["speed"]
            if "fireflies" in active:
                particle["x"] += math.sin(now / 500 + particle["phase"]) * 0.25
            if particle["y"] > self.canvas_rect.height:
                particle["y"] = 0
                particle["x"] = random.randint(0, max(1, self.canvas_rect.width - 1))
