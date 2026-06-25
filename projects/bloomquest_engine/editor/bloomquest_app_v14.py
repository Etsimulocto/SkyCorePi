# bloomquest_app_v14.py
# run with: imported by bloomquest_v14.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v14.py
# description: Adds persistent per-project color settings for the full BloomQuest interface.
# version: 0.14.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, settings, theme, colors, ui, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Colors use six-digit hexadecimal values and save inside project.json.
# uuid: bc-bloomquest-app-0014

from __future__ import annotations

import sys
from typing import Any

import pygame

from editor.bloomquest_app import (
    CANVAS_BOTTOM,
    CANVAS_LEFT,
    CANVAS_RIGHT,
    CANVAS_TOP,
    SELECTION,
    TILE_SIZE,
    TOP_BAR_HEIGHT,
    TextField,
)
from editor.bloomquest_app_v133 import BloomQuestAppV133


DEFAULT_THEME = {
    "background": "191C22",
    "panel": "23272F",
    "panel_alt": "2B303A",
    "field": "1A1E25",
    "text": "EBEEF4",
    "muted_text": "A5ACB8",
    "grid": "414854",
    "canvas": "14171C",
    "accent": "6EBE82",
    "selection": "F5D25A",
    "frame": "6EBE82",
    "item_stroke": "11151B",
    "status_bar": "2B303A",
}

THEME_CONSTANTS = {
    "background": "BACKGROUND",
    "panel": "PANEL",
    "panel_alt": "PANEL_ALT",
    "field": "FIELD",
    "text": "TEXT",
    "muted_text": "MUTED_TEXT",
    "grid": "GRID_LINE",
    "canvas": "CANVAS_COLOR",
    "accent": "ACCENT",
    "selection": "SELECTION",
}

THEME_LABELS = {
    "background": "Main Background",
    "panel": "Panel Background",
    "panel_alt": "Buttons / Status",
    "field": "Text Fields",
    "text": "Main Text",
    "muted_text": "Muted Text",
    "grid": "Grid Lines",
    "canvas": "Map Background",
    "accent": "Accent Buttons",
    "selection": "Selection Stroke",
    "frame": "Window / Menu Frame",
    "item_stroke": "Tile / Item Stroke",
    "status_bar": "Status Bar",
}


def hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    clean = value.strip().lstrip("#").upper()
    if len(clean) != 6:
        return fallback
    try:
        return tuple(int(clean[index:index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return fallback


def dynamic_draw_text(surface, text, x, y, font, color=None):
    if color is None:
        color = hex_to_rgb(DEFAULT_THEME["text"], (235, 238, 244))
    image = font.render(str(text), True, color)
    rect = image.get_rect(topleft=(x, y))
    surface.blit(image, rect)
    return rect


class BloomQuestAppV14(BloomQuestAppV133):
    """BloomQuest v0.14 with persistent project-specific visual themes."""

    def __init__(self) -> None:
        super().__init__()
        self.settings_button = pygame.Rect(1090, 10, 88, 34)
        self.play_button = pygame.Rect(1184, 10, 84, 34)
        self.settings_fields: list[TextField] = []
        self.settings_buttons: dict[str, pygame.Rect] = {}
        self.theme = dict(DEFAULT_THEME)
        self.load_project_theme()
        self.apply_theme()
        pygame.display.set_caption("BloomQuest Engine v0.14 — Theme Settings")
        self.status_message = "Settings added: full project color control."

    def load_project_theme(self) -> None:
        stored = self.project.get("theme", {}) if hasattr(self, "project") else {}
        for key, default in DEFAULT_THEME.items():
            value = str(stored.get(key, default)).strip().lstrip("#").upper()
            self.theme[key] = value if len(value) == 6 else default

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        self.theme = dict(DEFAULT_THEME)
        self.load_project_theme()
        self.apply_theme()

    def apply_theme(self) -> None:
        """Update every loaded BloomQuest editor module so inherited screens share one theme."""
        DEFAULT_THEME.update(self.theme)
        values = {key: hex_to_rgb(value, (255, 255, 255)) for key, value in self.theme.items()}

        for module_name, module in list(sys.modules.items()):
            if not module_name.startswith("editor.bloomquest_app"):
                continue
            for key, constant_name in THEME_CONSTANTS.items():
                if hasattr(module, constant_name):
                    setattr(module, constant_name, values[key])
            if hasattr(module, "draw_text"):
                setattr(module, "draw_text", dynamic_draw_text)

        self.theme_rgb = values

    def save_theme(self) -> None:
        for field in self.settings_fields:
            key = field.key.removeprefix("theme_")
            fallback = hex_to_rgb(DEFAULT_THEME[key], (255, 255, 255))
            rgb = hex_to_rgb(field.value, fallback)
            self.theme[key] = "".join(f"{channel:02X}" for channel in rgb)
            field.value = self.theme[key]

        self.project["theme"] = dict(self.theme)
        self.project_manager.save_project(self.project)
        self.apply_theme()
        self.status_message = "Theme saved to this project."

    def reset_theme(self) -> None:
        self.theme = dict(DEFAULT_THEME)
        self.build_settings_fields()
        self.save_theme()
        self.status_message = "Theme reset to BloomQuest defaults."

    def build_settings_fields(self) -> None:
        self.settings_fields = [
            TextField(f"theme_{key}", label, self.theme.get(key, DEFAULT_THEME[key]))
            for key, label in THEME_LABELS.items()
        ]

    def active_text_field(self):
        if self.overlay == "settings":
            return next((field for field in self.settings_fields if field.active), None)
        return super().active_text_field()

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.overlay == "settings":
            self.handle_settings_click(event.pos)
            return

        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            if self.settings_button.collidepoint(event.pos):
                self.build_settings_fields()
                self.overlay = "settings"
                return

        super().handle_click(event)

    def handle_settings_click(self, position: tuple[int, int]) -> None:
        for field in self.settings_fields:
            field.active = field.rect.collidepoint(position)

        if self.settings_buttons.get("apply", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.save_theme()
            return
        if self.settings_buttons.get("reset", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.reset_theme()
            return
        if self.settings_buttons.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay = None
            return

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        if self.mode != "edit":
            return

        panel_alt = self.theme_rgb["panel_alt"]
        text = self.theme_rgb["text"]
        pygame.draw.rect(self.screen, panel_alt, self.settings_button, border_radius=6)
        image = self.font_small.render("Settings", True, text)
        self.screen.blit(image, image.get_rect(center=self.settings_button.center))

        pygame.draw.rect(self.screen, self.theme_rgb["accent"], self.play_button, border_radius=6)
        image = self.font_small.render("▶ Play", True, self.theme_rgb["background"])
        self.screen.blit(image, image.get_rect(center=self.play_button.center))

    def draw_overlay(self) -> None:
        if self.overlay != "settings":
            super().draw_overlay()
            return
        self.draw_settings_overlay()

    def draw_settings_overlay(self) -> None:
        shade = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))

        box = pygame.Rect(205, 58, 950, 724)
        pygame.draw.rect(self.screen, self.theme_rgb["panel"], box, border_radius=10)
        pygame.draw.rect(self.screen, self.theme_rgb["frame"], box, 3, border_radius=10)
        dynamic_draw_text(self.screen, "Theme & Display Settings", box.x + 24, box.y + 18, self.font_title, self.theme_rgb["text"])
        dynamic_draw_text(self.screen, "Enter six-digit HEX colors. Example: 6EBE82", box.x + 26, box.y + 58, self.font_small, self.theme_rgb["muted_text"])

        self.settings_buttons = {}
        columns = 2
        field_width = 390
        row_height = 78
        start_y = box.y + 102

        for index, field in enumerate(self.settings_fields):
            column = index % columns
            row = index // columns
            x = box.x + 28 + column * 460
            y = start_y + row * row_height
            dynamic_draw_text(self.screen, field.label, x, y, self.font_small, self.theme_rgb["muted_text"])
            field.rect = pygame.Rect(x, y + 22, field_width, 38)
            pygame.draw.rect(self.screen, self.theme_rgb["field"], field.rect, border_radius=5)
            pygame.draw.rect(self.screen, self.theme_rgb["accent"] if field.active else self.theme_rgb["grid"], field.rect, 2, border_radius=5)
            preview = pygame.Rect(field.rect.right - 46, field.rect.y + 5, 32, 28)
            pygame.draw.rect(self.screen, hex_to_rgb(field.value, (255, 255, 255)), preview, border_radius=4)
            pygame.draw.rect(self.screen, self.theme_rgb["item_stroke"], preview, 2, border_radius=4)
            dynamic_draw_text(self.screen, field.value[-6:].upper(), field.rect.x + 10, field.rect.y + 8, self.font_small, self.theme_rgb["text"])

        button_y = box.bottom - 62
        apply_rect = pygame.Rect(box.x + 28, button_y, 180, 40)
        reset_rect = pygame.Rect(box.x + 220, button_y, 180, 40)
        close_rect = pygame.Rect(box.right - 148, button_y, 120, 40)
        self.settings_buttons = {"apply": apply_rect, "reset": reset_rect, "close": close_rect}

        for name, rect, label in (
            ("apply", apply_rect, "Apply & Save"),
            ("reset", reset_rect, "Reset Defaults"),
            ("close", close_rect, "Close"),
        ):
            fill = self.theme_rgb["accent"] if name == "apply" else self.theme_rgb["panel_alt"]
            foreground = self.theme_rgb["background"] if name == "apply" else self.theme_rgb["text"]
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def draw_item(self, surface: pygame.Surface, item: dict[str, Any], camera_x: int, camera_y: int, show_selection: bool) -> None:
        sx = CANVAS_LEFT + int(item.get("x", 0)) * TILE_SIZE - camera_x
        sy = CANVAS_TOP + int(item.get("y", 0)) * TILE_SIZE - camera_y
        if sx + TILE_SIZE < CANVAS_LEFT or sx > CANVAS_RIGHT or sy + TILE_SIZE < CANVAS_TOP or sy > CANVAS_BOTTOM:
            return

        rect = pygame.Rect(sx + 1, sy + 1, TILE_SIZE - 2, TILE_SIZE - 2)
        pygame.draw.rect(surface, tuple(item.get("color", [180, 180, 180])), rect, border_radius=3)
        pygame.draw.rect(surface, self.theme_rgb["item_stroke"], rect, 1, border_radius=3)

        emoji = item.get("emoji", "")
        if emoji:
            image = self.font_emoji.render(emoji, True, self.theme_rgb["text"])
            surface.blit(image, image.get_rect(center=rect.center))

        if show_selection and item is self.selected_instance:
            pygame.draw.rect(surface, self.theme_rgb["selection"], rect, 3, border_radius=3)

    def draw_status(self) -> None:
        pygame.draw.rect(self.screen, self.theme_rgb["status_bar"], (0, 810, 1360, 30))
        dynamic_draw_text(self.screen, self.status_message, 12, 817, self.font_small, self.theme_rgb["text"])
        right = "F1 Help | F5 Play | Ctrl+S Save" if self.mode == "edit" else "Esc Return to Edit"
        image = self.font_small.render(right, True, self.theme_rgb["muted_text"])
        self.screen.blit(image, image.get_rect(midright=(1348, 825)))
