# bloomquest_app_v081.py
# run with: imported by bloomquest_v081.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v081.py
# description: Fixes the dedicated Weapons palette label in BloomQuest v0.8.
# version: 0.8.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, palette, bugfix, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Uses the v0.8 five-layer labels instead of the inherited four-layer labels.
# uuid: bc-bloomquest-app-0008-1

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    CANVAS_BOTTOM,
    MUTED_TEXT,
    PALETTE_WIDTH,
    PANEL,
    PANEL_ALT,
    TEXT,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v08 import BloomQuestAppV08, LAYER_LABELS_V08


class BloomQuestAppV081(BloomQuestAppV08):
    """BloomQuest v0.8.1 palette-label fix."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.8.1")
        self.status_message = "v0.8.1 ready. Weapons and Effects now have separate working palettes."

    def draw_palette(self) -> None:
        """Draw the active five-layer part palette without legacy lookups."""
        pygame.draw.rect(
            self.screen,
            PANEL,
            (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, self.screen.get_height() - TOP_BAR_HEIGHT),
        )

        draw_text(self.screen, "Premade Parts", 14, TOP_BAR_HEIGHT + 12, self.font_medium)
        draw_text(
            self.screen,
            LAYER_LABELS_V08.get(self.active_layer, self.active_layer),
            14,
            TOP_BAR_HEIGHT + 36,
            self.font_small,
            MUTED_TEXT,
        )

        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll

        for row, (index, part) in enumerate(self.visible_parts()):
            y = start_y + row * 48
            if y + 42 < TOP_BAR_HEIGHT or y > CANVAS_BOTTOM:
                continue

            rect = pygame.Rect(10, y, PALETTE_WIDTH - 20, 42)
            selected = index == self.selected_part_index
            pygame.draw.rect(
                self.screen,
                (72, 83, 78) if selected else PANEL_ALT,
                rect,
                border_radius=5,
            )

            icon = pygame.Rect(16, y + 6, 30, 30)
            pygame.draw.rect(
                self.screen,
                tuple(part.get("color", [180, 180, 180])),
                icon,
                border_radius=4,
            )

            emoji = part.get("emoji", "")
            if emoji:
                image = self.font_emoji.render(emoji, True, TEXT)
                self.screen.blit(image, image.get_rect(center=icon.center))

            draw_text(
                self.screen,
                part.get("name", "Part"),
                54,
                y + 11,
                self.font_small,
            )

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        pygame.draw.rect(self.screen, PANEL, (0, 0, 245, TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.8.1", 12, 5, self.font_large)
        draw_text(self.screen, self.current_room_id, 14, 32, self.font_small, MUTED_TEXT)
