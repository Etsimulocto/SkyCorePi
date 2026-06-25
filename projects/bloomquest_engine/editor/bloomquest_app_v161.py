# bloomquest_app_v161.py
# run with: imported by bloomquest_v161.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v161.py
# description: Cleans up the BloomQuest header with compact title spacing and aligned controls.
# version: 0.16.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, header, toolbar, layout, ui, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Keeps every toolbar button aligned with its click target.
# uuid: bc-bloomquest-app-0016-1

from __future__ import annotations

import pygame

from editor.bloomquest_app import TOP_BAR_HEIGHT
from editor.bloomquest_app_v16 import BloomQuestAppV16
from editor.bloomquest_app_v14 import dynamic_draw_text


class BloomQuestAppV161(BloomQuestAppV16):
    """BloomQuest v0.16.1 with a compact, cleaned-up header."""

    HEADER_TITLE_WIDTH = 220
    LAYER_START_X = 226
    LAYER_WIDTH = 82
    LAYER_GAP = 5

    def __init__(self) -> None:
        super().__init__()

        self.project_button = pygame.Rect(754, 9, 76, 34)
        self.rooms_button = pygame.Rect(835, 9, 68, 34)
        self.game_button = pygame.Rect(908, 9, 66, 34)
        self.maps_button = pygame.Rect(979, 9, 66, 34)
        self.settings_button = pygame.Rect(1050, 9, 82, 34)
        self.help_button = pygame.Rect(1137, 9, 62, 34)
        self.play_button = pygame.Rect(1204, 9, 78, 34)

        pygame.display.set_caption("BloomQuest Engine v0.16.1")
        self.status_message = "Header cleaned up and controls aligned."

    def layer_button_rects_v161(self):
        layers = (
            "map",
            "scene_objects",
            "decorations",
            "actors",
            "weapons",
            "weapons_effects",
        )
        x = self.LAYER_START_X
        rects = []
        for layer in layers:
            rects.append((layer, pygame.Rect(x, 9, self.LAYER_WIDTH, 34)))
            x += self.LAYER_WIDTH + self.LAYER_GAP
        return rects

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            position = event.pos

            for layer, rect in self.layer_button_rects_v161():
                if rect.collidepoint(position):
                    self.set_layer(layer)
                    return

            if self.project_button.collidepoint(position):
                self.overlay = "projects"
                self.overlay_scroll = 0
                return
            if self.rooms_button.collidepoint(position):
                self.overlay = "rooms"
                self.overlay_scroll = 0
                return
            if self.game_button.collidepoint(position):
                self.build_game_fields()
                self.overlay = "game_settings"
                return
            if self.maps_button.collidepoint(position):
                self.overlay = "map_generator"
                self.rebuild_generator_preview()
                return
            if self.settings_button.collidepoint(position):
                self.build_settings_fields()
                self.overlay = "settings"
                return
            if self.help_button.collidepoint(position):
                self.overlay = "help"
                self.overlay_scroll = 0
                return
            if self.play_button.collidepoint(position):
                self.enter_play_mode()
                return
            return

        super().handle_click(event)

    def draw_top_bar(self) -> None:
        panel = self.theme_rgb["panel"]
        panel_alt = self.theme_rgb["panel_alt"]
        accent = self.theme_rgb["accent"]
        text = self.theme_rgb["text"]
        muted = self.theme_rgb["muted_text"]
        background = self.theme_rgb["background"]

        pygame.draw.rect(self.screen, panel, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))

        dynamic_draw_text(self.screen, "BloomQuest", 12, 3, self.font_large, text)
        dynamic_draw_text(self.screen, "v0.16.1", 145, 8, self.font_small, accent)
        dynamic_draw_text(self.screen, self.project_id, 14, 31, self.font_small, muted)

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

        for layer, rect in self.layer_button_rects_v161():
            selected = layer == self.active_layer
            pygame.draw.rect(self.screen, accent if selected else panel_alt, rect, border_radius=6)
            foreground = background if selected else text
            image = self.font_small.render(labels[layer], True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))

        buttons = (
            (self.project_button, "Projects", False),
            (self.rooms_button, "Rooms", False),
            (self.game_button, "Game", False),
            (self.maps_button, "Maps", False),
            (self.settings_button, "Settings", False),
            (self.help_button, "Help", False),
            (self.play_button, "▶ Play", True),
        )

        for rect, label, primary in buttons:
            fill = accent if primary else panel_alt
            foreground = background if primary else text
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))
