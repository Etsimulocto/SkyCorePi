# bloomquest_app_v132.py
# run with: imported by bloomquest_v132.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v132.py
# description: Scales BloomQuest to fill the entire resizable window with correct mouse mapping.
# version: 0.13.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, window, scaling, fullscreen, resize, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Uses the full client area instead of letterboxing.
# uuid: bc-bloomquest-app-0013-2

from __future__ import annotations

import pygame

from editor.bloomquest_app import WINDOW_HEIGHT, WINDOW_WIDTH
from editor.bloomquest_app_v131 import BloomQuestAppV131


class BloomQuestAppV132(BloomQuestAppV131):
    """BloomQuest v0.13.2 with full-window scaling."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.13.2 — Full Window")
        self.status_message = "The editor now fills the entire resizable window."

    def present_scaled(self) -> None:
        """Stretch the logical editor surface to the complete window area."""
        window_width, window_height = self.display_surface.get_size()
        self.render_rect = pygame.Rect(0, 0, window_width, window_height)

        scaled = pygame.transform.smoothscale(
            self.logical_surface,
            (window_width, window_height),
        )
        self.display_surface.blit(scaled, (0, 0))

    def screen_to_logical(self, position: tuple[int, int]) -> tuple[int, int] | None:
        """Translate full-window mouse coordinates into logical editor coordinates."""
        window_width, window_height = self.display_surface.get_size()
        if window_width <= 0 or window_height <= 0:
            return None

        logical_x = int(position[0] * WINDOW_WIDTH / window_width)
        logical_y = int(position[1] * WINDOW_HEIGHT / window_height)

        logical_x = max(0, min(WINDOW_WIDTH - 1, logical_x))
        logical_y = max(0, min(WINDOW_HEIGHT - 1, logical_y))
        return logical_x, logical_y
