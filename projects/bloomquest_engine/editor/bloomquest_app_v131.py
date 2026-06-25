# bloomquest_app_v131.py
# run with: imported by bloomquest_v131.py
# description: Fixes editor rendering and topmost selection for the Decorations layer.
# version: 0.13.1
# updated: 2026-06-25

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    CANVAS_BOTTOM,
    CANVAS_COLOR,
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_RIGHT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    GRID_LINE,
    TILE_SIZE,
)
from editor.bloomquest_app_v13 import BloomQuestAppV13


class BloomQuestAppV131(BloomQuestAppV13):
    """BloomQuest v0.13.1 with Decorations visible in Edit Mode."""

    EDITOR_LAYER_ORDER = (
        "map",
        "scene_objects",
        "decorations",
        "actors",
        "weapons",
        "weapons_effects",
    )

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.13.1 — Decorations Fix")
        self.status_message = "Decorations now render immediately in Edit Mode."

    def draw_canvas(self) -> None:
        rect = pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, CANVAS_COLOR, rect)
        self.screen.set_clip(rect)

        start_x = self.camera_x // TILE_SIZE
        start_y = self.camera_y // TILE_SIZE
        for gy in range(start_y, start_y + CANVAS_HEIGHT // TILE_SIZE + 2):
            for gx in range(start_x, start_x + CANVAS_WIDTH // TILE_SIZE + 2):
                sx = CANVAS_LEFT + gx * TILE_SIZE - self.camera_x
                sy = CANVAS_TOP + gy * TILE_SIZE - self.camera_y
                pygame.draw.rect(self.screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

        for layer in self.EDITOR_LAYER_ORDER:
            for item in self.room.get("layers", {}).get(layer, []):
                self.draw_item(self.screen, item, self.camera_x, self.camera_y, True)

        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, rect, 1)

    def find_at(self, gx: int, gy: int, layer: str | None = None):
        layers = [layer] if layer else list(reversed(self.EDITOR_LAYER_ORDER))
        for current_layer in layers:
            for item in reversed(self.room.get("layers", {}).get(current_layer, [])):
                if item.get("x") == gx and item.get("y") == gy:
                    return item
        return None
