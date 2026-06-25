# bloomquest_app_v171.py
# run with: imported by bloomquest_v171.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v171.py
# description: Finalizes overlay control mappings and updates the compact header for BloomQuest v0.17.1.
# version: 0.17.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, overlay, controls, header, lighting, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Fixes player-light radius and softness plus/minus controls.
# uuid: bc-bloomquest-app-0017-1

from __future__ import annotations

import pygame

from editor.bloomquest_app import TOP_BAR_HEIGHT
from editor.bloomquest_app_v14 import dynamic_draw_text
from editor.bloomquest_app_v17 import BloomQuestAppV17


class BloomQuestAppV171(BloomQuestAppV17):
    """BloomQuest v0.17.1 polished overlay build."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.17.1 — Overlays & Lighting")
        self.status_message = "Overlays ready: darkness, textures, vignette, fog, and dynamic lights."

    def handle_overlay_settings_click(self, position: tuple[int, int]) -> None:
        for overlay_type, rect in self.overlay_type_rects:
            if rect.collidepoint(position):
                self.set_overlay_type(overlay_type)
                return

        adjustments = {
            "opacity_minus": ("opacity", -15, 0, 255),
            "opacity_plus": ("opacity", 15, 0, 255),
            "texture_minus": ("texture_strength", -10, 0, 100),
            "texture_plus": ("texture_strength", 10, 0, 100),
            "vignette_minus": ("vignette", -10, 0, 100),
            "vignette_plus": ("vignette", 10, 0, 100),
            "player_minus": ("player_light_radius", -1, 1, 12),
            "player_plus": ("player_light_radius", 1, 1, 12),
            "light_minus": ("light_softness", -10, 10, 100),
            "light_plus": ("light_softness", 10, 10, 100),
        }
        for name, args in adjustments.items():
            rect = self.overlay_control_rects.get(name, pygame.Rect(0, 0, 0, 0))
            if rect.collidepoint(position):
                self.adjust_overlay_value(*args)
                return

        editor_rect = self.overlay_control_rects.get("editor_preview", pygame.Rect(0, 0, 0, 0))
        if editor_rect.collidepoint(position):
            self.overlay_config["editor_preview"] = not bool(self.overlay_config.get("editor_preview", True))
            return

        play_rect = self.overlay_control_rects.get("play_enabled", pygame.Rect(0, 0, 0, 0))
        if play_rect.collidepoint(position):
            self.overlay_config["play_enabled"] = not bool(self.overlay_config.get("play_enabled", True))
            return

        if self.overlay_action_rects.get("save", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.save_overlay_config()
            return
        if self.overlay_action_rects.get("reset", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay_config = self.default_overlay_config()
            self.status_message = "Overlay reset to defaults."
            return
        if self.overlay_action_rects.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay = None

    def draw_top_bar(self) -> None:
        panel = self.theme_rgb["panel"]
        panel_alt = self.theme_rgb["panel_alt"]
        accent = self.theme_rgb["accent"]
        text = self.theme_rgb["text"]
        muted = self.theme_rgb["muted_text"]
        background = self.theme_rgb["background"]

        pygame.draw.rect(self.screen, panel, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        dynamic_draw_text(self.screen, "BloomQuest", 12, 3, self.font_large, text)
        dynamic_draw_text(self.screen, "v0.17.1", 145, 8, self.font_small, accent)
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
            image = self.font_small.render(labels[layer], True, background if selected else text)
            self.screen.blit(image, image.get_rect(center=rect.center))

        buttons = (
            (self.project_button, "Projects", False),
            (self.rooms_button, "Rooms", False),
            (self.game_button, "Game", False),
            (self.maps_button, "Maps", False),
            (self.overlay_button, "Overlay", False),
            (self.settings_button, "Settings", False),
            (self.help_button, "Help", False),
            (self.play_button, "▶ Play", True),
        )
        for rect, label, primary in buttons:
            pygame.draw.rect(self.screen, accent if primary else panel_alt, rect, border_radius=6)
            image = self.font_small.render(label, True, background if primary else text)
            self.screen.blit(image, image.get_rect(center=rect.center))
