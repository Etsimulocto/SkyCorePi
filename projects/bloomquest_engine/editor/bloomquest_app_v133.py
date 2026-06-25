# bloomquest_app_v133.py
# run with: imported by bloomquest_v133.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v133.py
# description: Repositions top-bar controls so the map button never overlaps the BloomQuest title.
# version: 0.13.3
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, ui, toolbar, title, layout, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Keeps all toolbar hitboxes aligned with the drawn buttons.
# uuid: bc-bloomquest-app-0013-3

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    MUTED_TEXT,
    PANEL,
    PANEL_ALT,
    TEXT,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v132 import BloomQuestAppV132


class BloomQuestAppV133(BloomQuestAppV132):
    """BloomQuest v0.13.3 with a clean non-overlapping toolbar."""

    LAYER_BUTTON_X = 270
    LAYER_BUTTON_WIDTH = 86
    LAYER_BUTTON_GAP = 6

    def __init__(self) -> None:
        super().__init__()

        self.project_button = pygame.Rect(830, 10, 92, 34)
        self.rooms_button = pygame.Rect(928, 10, 78, 34)
        self.help_button = pygame.Rect(1012, 10, 72, 34)
        self.play_button = pygame.Rect(1090, 10, 84, 34)

        pygame.display.set_caption("BloomQuest Engine v0.13.3 — Toolbar Fix")
        self.status_message = "Top bar spacing fixed."

    def layer_button_rects(self):
        layers = (
            "map",
            "scene_objects",
            "decorations",
            "actors",
            "weapons",
            "weapons_effects",
        )
        rects = []
        x = self.LAYER_BUTTON_X
        for layer in layers:
            rects.append((layer, pygame.Rect(x, 10, self.LAYER_BUTTON_WIDTH, 34)))
            x += self.LAYER_BUTTON_WIDTH + self.LAYER_BUTTON_GAP
        return rects

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            x, y = event.pos

            if self.project_button.collidepoint(x, y):
                self.overlay = "projects"
                self.overlay_scroll = 0
                return
            if self.rooms_button.collidepoint(x, y):
                self.overlay = "rooms"
                self.overlay_scroll = 0
                return
            if self.help_button.collidepoint(x, y):
                self.overlay = "help"
                self.overlay_scroll = 0
                return
            if self.play_button.collidepoint(x, y):
                self.enter_play_mode()
                return

            for layer, rect in self.layer_button_rects():
                if rect.collidepoint(x, y):
                    self.set_layer(layer)
                    return
            return

        super().handle_click(event)

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))

        title_cover = pygame.Rect(0, 0, 260, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL, title_cover)
        draw_text(self.screen, "BloomQuest v0.13.3", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

        if self.mode != "edit":
            return

        labels = {
            "map": "Map",
            "scene_objects": "Objects",
            "decorations": "Decor",
            "actors": "Actors",
            "weapons": "Weapons",
            "weapons_effects": "Effects",
        }

        for layer, rect in self.layer_button_rects():
            active = layer == self.active_layer
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(labels[layer], True, BACKGROUND if active else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))

        for rect, label in (
            (self.project_button, "Projects"),
            (self.rooms_button, "Rooms"),
            (self.help_button, "Help"),
            (self.play_button, "▶ Play"),
        ):
            active = label == "▶ Play"
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND if active else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))
