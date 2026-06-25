# world_play_v181.py
# run with: imported by editor/bloomquest_app_v181.py
# path: projects/bloomquest_engine/engine/world_play_v181.py
# description: Displays the BloomQuest Adventure 001 cover art on the title screen.
# version: 0.18.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, cover, title-screen, artwork, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Searches engine assets, project assets, and the user's Downloads folder.
# uuid: bc-bloomquest-worldplay-0018-1

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pygame

from engine.world_play_v18 import WorldPlayV18


COVER_FILENAME = "BloomQuest_Cover_Adventure_001.png"


class WorldPlayV181(WorldPlayV18):
    """BloomQuest runtime with a full illustrated cover title screen."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cover_source = self.find_cover_path()
        self.cover_image = self.load_cover_image(self.cover_source)

    def find_cover_path(self) -> Path | None:
        configured = str(self.game_config.get("cover_image", "")).strip()
        engine_root = Path(__file__).resolve().parent.parent
        home = Path.home()

        candidates = []
        if configured:
            configured_path = Path(os.path.expandvars(os.path.expanduser(configured)))
            candidates.append(configured_path)
            candidates.append(engine_root / configured_path)

        candidates.extend(
            [
                engine_root / "assets" / COVER_FILENAME,
                engine_root / "data" / "art" / COVER_FILENAME,
                home / "BloomQuestProjects" / "Adventure_001" / "assets" / COVER_FILENAME,
                home / "Downloads" / COVER_FILENAME,
                home / "Desktop" / COVER_FILENAME,
            ]
        )

        for candidate in candidates:
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
        return None

    @staticmethod
    def load_cover_image(path: Path | None) -> pygame.Surface | None:
        if path is None:
            return None
        try:
            return pygame.image.load(str(path)).convert()
        except (pygame.error, OSError):
            return None

    @staticmethod
    def cover_crop(image: pygame.Surface, target: pygame.Rect) -> pygame.Surface:
        """Scale an image to fill a rectangle, then crop it from the center."""
        source_width, source_height = image.get_size()
        scale = max(target.width / source_width, target.height / source_height)
        scaled_size = (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )
        scaled = pygame.transform.smoothscale(image, scaled_size)
        crop = pygame.Rect(0, 0, target.width, target.height)
        crop.center = scaled.get_rect().center
        return scaled.subsurface(crop).copy()

    def draw_title_screen(self, surface: pygame.Surface, colors: dict[str, tuple[int, int, int]]) -> None:
        if self.cover_image is None:
            super().draw_title_screen(surface, colors)
            return

        cover = self.cover_crop(self.cover_image, self.canvas_rect)
        surface.blit(cover, self.canvas_rect.topleft)

        # Dark edge treatment keeps menu text readable without hiding the artwork.
        shade = pygame.Surface(self.canvas_rect.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 24))
        pygame.draw.rect(
            shade,
            (0, 0, 0, 150),
            (0, self.canvas_rect.height - 175, self.canvas_rect.width, 175),
        )
        pygame.draw.rect(
            shade,
            (0, 0, 0, 55),
            (0, 0, self.canvas_rect.width, 95),
        )
        surface.blit(shade, self.canvas_rect.topleft)

        objective_panel = pygame.Rect(0, 0, 680, 118)
        objective_panel.midbottom = (
            self.canvas_rect.centerx,
            self.canvas_rect.bottom - 24,
        )
        panel_surface = pygame.Surface(objective_panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surface,
            (*colors["panel"], 225),
            panel_surface.get_rect(),
            border_radius=12,
        )
        pygame.draw.rect(
            panel_surface,
            colors["accent"],
            panel_surface.get_rect(),
            3,
            border_radius=12,
        )
        surface.blit(panel_surface, objective_panel.topleft)

        objective_image = self.subtitle_font.render(
            f"Objective: {self.objective_text()}",
            True,
            colors["accent"],
        )
        surface.blit(
            objective_image,
            objective_image.get_rect(center=(objective_panel.centerx, objective_panel.y + 35)),
        )

        pulse = 185 + int(70 * abs(pygame.time.get_ticks() % 1200 - 600) / 600)
        start_color = tuple(min(255, channel * pulse // 210) for channel in colors["text"])
        start_image = self.menu_font.render(
            "Press Enter / Space / A to Start",
            True,
            start_color,
        )
        surface.blit(
            start_image,
            start_image.get_rect(center=(objective_panel.centerx, objective_panel.y + 78)),
        )

        if self.cover_source is not None:
            source_label = self.subtitle_font.render(
                "BloomQuest Adventure 001",
                True,
                (220, 228, 238),
            )
            surface.blit(
                source_label,
                (self.canvas_rect.x + 18, self.canvas_rect.y + 14),
            )
