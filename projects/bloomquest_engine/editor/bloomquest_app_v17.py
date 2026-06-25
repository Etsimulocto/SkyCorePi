# bloomquest_app_v17.py
# run with: imported by bloomquest_v17.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v17.py
# description: Adds project overlay settings, editor preview, darkness, texture, vignette, and dynamic-light controls.
# version: 0.17.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, overlays, darkness, fog, lighting, settings, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Overlay settings save inside project.json and apply in Edit and Play modes.
# uuid: bc-bloomquest-app-0017

from __future__ import annotations

from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    TILE_SIZE,
    TOP_BAR_HEIGHT,
)
from editor.bloomquest_app_v14 import dynamic_draw_text
from editor.bloomquest_app_v161 import BloomQuestAppV161
from engine.world_play_v17 import OVERLAY_PRESETS, WorldPlayV17


class BloomQuestAppV17(BloomQuestAppV161):
    """BloomQuest v0.17 with cinematic room overlays and dynamic lights."""

    OVERLAY_INFO = {
        "none": ("None", "No room overlay"),
        "night": ("Night", "Dark blue evening tint"),
        "cave": ("Cave", "Darkness with player and object lights"),
        "fog": ("Fog", "Moving pale haze"),
        "dust": ("Dust", "Warm floating particles"),
        "underwater": ("Underwater", "Blue wash with wave bands"),
        "heat": ("Heat", "Orange tint and shimmer"),
        "poison": ("Poison", "Green toxic haze"),
        "dream": ("Dream", "Purple glow and drifting motes"),
        "old_film": ("Old Film", "Sepia grain and scratches"),
        "storm": ("Storm", "Dark rain and lightning flashes"),
    }

    def __init__(self) -> None:
        super().__init__()

        self.project_button = pygame.Rect(720, 9, 70, 34)
        self.rooms_button = pygame.Rect(795, 9, 62, 34)
        self.game_button = pygame.Rect(862, 9, 60, 34)
        self.maps_button = pygame.Rect(927, 9, 60, 34)
        self.overlay_button = pygame.Rect(992, 9, 72, 34)
        self.settings_button = pygame.Rect(1069, 9, 78, 34)
        self.help_button = pygame.Rect(1152, 9, 58, 34)
        self.play_button = pygame.Rect(1215, 9, 74, 34)

        self.overlay_config = self.default_overlay_config()
        self.load_overlay_config()
        self.overlay_type_rects: list[tuple[str, pygame.Rect]] = []
        self.overlay_control_rects: dict[str, pygame.Rect] = {}
        self.overlay_action_rects: dict[str, pygame.Rect] = {}

        pygame.display.set_caption("BloomQuest Engine v0.17 — Overlays & Lighting")
        self.status_message = "Overlay menu ready: darkness, texture, fog, vignette, and dynamic lights."

    def default_overlay_config(self) -> dict:
        return {
            "type": "none",
            "color": [20, 35, 85],
            "opacity": 105,
            "texture_strength": 30,
            "vignette": 25,
            "player_light_radius": 5,
            "light_softness": 70,
            "editor_preview": True,
            "play_enabled": True,
            "lightning_interval_ms": 4500,
        }

    def load_overlay_config(self) -> None:
        config = self.default_overlay_config()
        config.update(deepcopy(self.project.get("overlay", {})))
        if config.get("type") not in self.OVERLAY_INFO:
            config["type"] = "none"
        self.overlay_config = config

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        self.load_overlay_config()

    def save_overlay_config(self) -> None:
        self.project["overlay"] = deepcopy(self.overlay_config)
        self.project_manager.save_project(self.project)
        self.status_message = "Room overlay saved to this project."

    def set_overlay_type(self, overlay_type: str) -> None:
        self.overlay_config["type"] = overlay_type
        color, alpha = OVERLAY_PRESETS.get(overlay_type, OVERLAY_PRESETS["none"])
        self.overlay_config["color"] = list(color)
        self.overlay_config["opacity"] = alpha
        self.status_message = f"Overlay: {self.OVERLAY_INFO[overlay_type][0]}"

    def adjust_overlay_value(self, key: str, amount: int, low: int, high: int) -> None:
        current = int(self.overlay_config.get(key, low))
        self.overlay_config[key] = max(low, min(high, current + amount))

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.overlay == "overlay_settings":
            self.handle_overlay_settings_click(event.pos)
            return

        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            if self.overlay_button.collidepoint(event.pos):
                self.overlay = "overlay_settings"
                return

        super().handle_click(event)

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
            "radius_minus": ("player_light_radius", -1, 1, 12),
            "radius_plus": ("player_light_radius", 1, 1, 12),
            "softness_minus": ("light_softness", -10, 10, 100),
            "softness_plus": ("light_softness", 10, 10, 100),
        }
        for name, args in adjustments.items():
            if self.overlay_control_rects.get(name, pygame.Rect(0, 0, 0, 0)).collidepoint(position):
                self.adjust_overlay_value(*args)
                return

        if self.overlay_control_rects.get("editor_preview", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay_config["editor_preview"] = not bool(self.overlay_config.get("editor_preview", True))
            return
        if self.overlay_control_rects.get("play_enabled", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
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
            return

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        if self.mode != "edit":
            return

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
            fill = self.theme_rgb["accent"] if primary else self.theme_rgb["panel_alt"]
            foreground = self.theme_rgb["background"] if primary else self.theme_rgb["text"]
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def draw_canvas(self) -> None:
        super().draw_canvas()
        if self.overlay_config.get("editor_preview", True):
            self.draw_editor_overlay_preview()

    def draw_editor_overlay_preview(self) -> None:
        overlay_type = str(self.overlay_config.get("type", "none"))
        if overlay_type == "none":
            return

        color = tuple(self.overlay_config.get("color", [20, 35, 85]))
        alpha = max(0, min(255, int(self.overlay_config.get("opacity", 105))))
        layer = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SRCALPHA)
        layer.fill((*color, alpha))

        if overlay_type == "cave":
            player = next(
                (item for item in self.room.get("layers", {}).get("actors", []) if item.get("part_id") == "player"),
                None,
            )
            if player:
                center = (
                    int(player.get("x", 0)) * TILE_SIZE - self.camera_x + TILE_SIZE // 2,
                    int(player.get("y", 0)) * TILE_SIZE - self.camera_y + TILE_SIZE // 2,
                )
                radius = int(self.overlay_config.get("player_light_radius", 5)) * TILE_SIZE
                pygame.draw.circle(layer, (0, 0, 0, 0), center, radius)

        self.screen.blit(layer, (CANVAS_LEFT, CANVAS_TOP))

        vignette = int(self.overlay_config.get("vignette", 25))
        if vignette:
            frame = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SRCALPHA)
            alpha_value = int(150 * vignette / 100)
            pygame.draw.rect(frame, (0, 0, 0, alpha_value), frame.get_rect(), 28, border_radius=24)
            self.screen.blit(frame, (CANVAS_LEFT, CANVAS_TOP))

    def draw_overlay(self) -> None:
        if self.overlay != "overlay_settings":
            super().draw_overlay()
            return
        self.draw_overlay_settings()

    def draw_overlay_settings(self) -> None:
        shade = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))

        box = pygame.Rect(130, 62, 1100, 716)
        pygame.draw.rect(self.screen, self.theme_rgb["panel"], box, border_radius=10)
        pygame.draw.rect(self.screen, self.theme_rgb["frame"], box, 3, border_radius=10)
        dynamic_draw_text(self.screen, "Map Overlay & Dynamic Lighting", box.x + 24, box.y + 18, self.font_title, self.theme_rgb["text"])
        dynamic_draw_text(
            self.screen,
            "Choose an atmosphere, then tune darkness, texture, vignette, and player light.",
            box.x + 26,
            box.y + 60,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        self.overlay_type_rects = []
        left_x = box.x + 24
        start_y = box.y + 98
        card_width = 320
        card_height = 48
        for index, (overlay_type, (title, description)) in enumerate(self.OVERLAY_INFO.items()):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(left_x + column * 330, start_y + row * 54, card_width, card_height)
            selected = overlay_type == self.overlay_config.get("type")
            pygame.draw.rect(self.screen, self.theme_rgb["accent"] if selected else self.theme_rgb["panel_alt"], rect, border_radius=6)
            pygame.draw.rect(self.screen, self.theme_rgb["frame"] if selected else self.theme_rgb["grid"], rect, 2, border_radius=6)
            foreground = self.theme_rgb["background"] if selected else self.theme_rgb["text"]
            secondary = self.theme_rgb["background"] if selected else self.theme_rgb["muted_text"]
            dynamic_draw_text(self.screen, title, rect.x + 12, rect.y + 6, self.font_small, foreground)
            dynamic_draw_text(self.screen, description, rect.x + 12, rect.y + 26, self.font_small, secondary)
            self.overlay_type_rects.append((overlay_type, rect))

        controls_x = box.x + 700
        controls_y = box.y + 106
        self.overlay_control_rects = {}

        controls = (
            ("opacity", "Opacity", 0, 255),
            ("texture_strength", "Texture Strength", 0, 100),
            ("vignette", "Vignette", 0, 100),
            ("player_light_radius", "Player Light Radius", 1, 12),
            ("light_softness", "Light Softness", 10, 100),
        )

        for index, (key, label, low, high) in enumerate(controls):
            y = controls_y + index * 88
            value = int(self.overlay_config.get(key, low))
            dynamic_draw_text(self.screen, label, controls_x, y, self.font_medium, self.theme_rgb["text"])
            minus = pygame.Rect(controls_x, y + 32, 42, 36)
            value_rect = pygame.Rect(controls_x + 50, y + 32, 150, 36)
            plus = pygame.Rect(controls_x + 208, y + 32, 42, 36)
            for rect, text in ((minus, "−"), (plus, "+")):
                pygame.draw.rect(self.screen, self.theme_rgb["panel_alt"], rect, border_radius=5)
                image = self.font_medium.render(text, True, self.theme_rgb["text"])
                self.screen.blit(image, image.get_rect(center=rect.center))
            pygame.draw.rect(self.screen, self.theme_rgb["field"], value_rect, border_radius=5)
            image = self.font_small.render(str(value), True, self.theme_rgb["text"])
            self.screen.blit(image, image.get_rect(center=value_rect.center))
            self.overlay_control_rects[f"{key.split('_')[0]}_minus"] = minus
            self.overlay_control_rects[f"{key.split('_')[0]}_plus"] = plus

        toggle_y = controls_y + 460
        for index, (key, label) in enumerate((
            ("editor_preview", "Preview in Editor"),
            ("play_enabled", "Enable in Play Mode"),
        )):
            rect = pygame.Rect(controls_x, toggle_y + index * 46, 250, 38)
            enabled = bool(self.overlay_config.get(key, True))
            pygame.draw.rect(self.screen, self.theme_rgb["accent"] if enabled else self.theme_rgb["panel_alt"], rect, border_radius=6)
            foreground = self.theme_rgb["background"] if enabled else self.theme_rgb["text"]
            image = self.font_small.render(f"{'✓' if enabled else '○'} {label}", True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))
            self.overlay_control_rects[key] = rect

        save = pygame.Rect(box.x + 24, box.bottom - 58, 160, 40)
        reset = pygame.Rect(box.x + 196, box.bottom - 58, 150, 40)
        close = pygame.Rect(box.right - 120, box.bottom - 58, 96, 40)
        self.overlay_action_rects = {"save": save, "reset": reset, "close": close}

        for name, rect, label in (
            ("save", save, "Save Overlay"),
            ("reset", reset, "Reset"),
            ("close", close, "Close"),
        ):
            primary = name == "save"
            fill = self.theme_rgb["accent"] if primary else self.theme_rgb["panel_alt"]
            foreground = self.theme_rgb["background"] if primary else self.theme_rgb["text"]
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def enter_play_mode(self) -> None:
        self.repair_equipment()
        self.save_current_room()

        has_player = any(
            item.get("part_id") == "player"
            for item in self.room.get("layers", {}).get("actors", [])
        )
        if not has_player:
            self.status_message = "Place a Player in this room first."
            return

        overlay_config = deepcopy(self.overlay_config)
        if not overlay_config.get("play_enabled", True):
            overlay_config["type"] = "none"

        self.world_play = WorldPlayV17(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
            game_config=deepcopy(self.game_config),
            overlay_config=overlay_config,
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.17 — PLAY MODE")

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend([
                "## Add a Map Overlay",
                "66. Open Overlay from the top bar.",
                "67. Choose Night, Cave, Fog, Dust, Underwater, Heat, Poison, Dream, Old Film, or Storm.",
                "68. Adjust opacity, texture, vignette, light radius, and softness.",
                "69. Enable Editor Preview to see the overlay while building.",
                "70. Cave lights react to the player, torches, runes, projectiles, bombs, and explosions.",
            ])
        else:
            content.extend([
                "## Overlays and Dynamic Lights",
                "Room overlays tint and texture the whole map without changing tiles.",
                "Cave darkness is cut away by moving and placed light sources.",
            ])
        return content
