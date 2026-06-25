# bloomquest_app_v141.py
# run with: imported by bloomquest_v141.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v141.py
# description: Replaces hexadecimal theme entry with a visual hue and shade color picker.
# version: 0.14.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, settings, color-picker, theme, ui, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Click a theme target, choose a hue, then choose saturation and brightness.
# uuid: bc-bloomquest-app-0014-1

from __future__ import annotations

import colorsys

import pygame

from editor.bloomquest_app_v14 import (
    DEFAULT_THEME,
    THEME_LABELS,
    BloomQuestAppV14,
    dynamic_draw_text,
    hex_to_rgb,
)


class BloomQuestAppV141(BloomQuestAppV14):
    """BloomQuest v0.14.1 with a mouse-driven visual color picker."""

    def __init__(self) -> None:
        super().__init__()
        self.settings_fields = []
        self.selected_theme_key = "accent"
        self.picker_hue = 0.36
        self.picker_saturation = 0.42
        self.picker_value = 0.75

        self.theme_target_rects: list[tuple[str, pygame.Rect]] = []
        self.hue_rect = pygame.Rect(0, 0, 0, 0)
        self.shade_rect = pygame.Rect(0, 0, 0, 0)
        self.settings_buttons = {}

        self.hue_surface: pygame.Surface | None = None
        self.shade_surface: pygame.Surface | None = None
        self.shade_surface_hue = -1.0

        self.load_picker_from_selected()
        pygame.display.set_caption("BloomQuest Engine v0.14.1 — Visual Color Picker")
        self.status_message = "Theme colors now use a visual picker instead of HEX entry."

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return "".join(f"{channel:02X}" for channel in rgb)

    def load_picker_from_selected(self) -> None:
        rgb = hex_to_rgb(self.theme.get(self.selected_theme_key, "FFFFFF"), (255, 255, 255))
        red, green, blue = (channel / 255.0 for channel in rgb)
        hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
        self.picker_hue = hue
        self.picker_saturation = saturation
        self.picker_value = value
        self.shade_surface_hue = -1.0

    def picker_rgb(self) -> tuple[int, int, int]:
        red, green, blue = colorsys.hsv_to_rgb(
            self.picker_hue,
            self.picker_saturation,
            self.picker_value,
        )
        return round(red * 255), round(green * 255), round(blue * 255)

    def set_selected_color_from_picker(self) -> None:
        self.theme[self.selected_theme_key] = self.rgb_to_hex(self.picker_rgb())
        self.apply_theme()

    def build_settings_fields(self) -> None:
        """The visual picker replaces text fields entirely."""
        self.settings_fields = []
        self.theme_target_rects = []
        if self.selected_theme_key not in THEME_LABELS:
            self.selected_theme_key = "accent"
        self.load_picker_from_selected()

    def active_text_field(self):
        if self.overlay == "settings":
            return None
        return super().active_text_field()

    def save_theme(self) -> None:
        self.project["theme"] = dict(self.theme)
        self.project_manager.save_project(self.project)
        self.apply_theme()
        self.status_message = "Theme saved to this project."

    def reset_theme(self) -> None:
        self.theme = dict(DEFAULT_THEME)
        self.selected_theme_key = "accent"
        self.load_picker_from_selected()
        self.save_theme()
        self.status_message = "Theme reset to BloomQuest defaults."

    def handle_settings_click(self, position: tuple[int, int]) -> None:
        for key, rect in self.theme_target_rects:
            if rect.collidepoint(position):
                self.selected_theme_key = key
                self.load_picker_from_selected()
                self.status_message = f"Editing {THEME_LABELS[key]}"
                return

        if self.hue_rect.collidepoint(position):
            relative = position[0] - self.hue_rect.x
            self.picker_hue = max(0.0, min(1.0, relative / max(1, self.hue_rect.width - 1)))
            self.shade_surface_hue = -1.0
            self.set_selected_color_from_picker()
            return

        if self.shade_rect.collidepoint(position):
            relative_x = position[0] - self.shade_rect.x
            relative_y = position[1] - self.shade_rect.y
            self.picker_saturation = max(0.0, min(1.0, relative_x / max(1, self.shade_rect.width - 1)))
            self.picker_value = max(0.0, min(1.0, 1.0 - relative_y / max(1, self.shade_rect.height - 1)))
            self.set_selected_color_from_picker()
            return

        if self.settings_buttons.get("apply", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.save_theme()
            return
        if self.settings_buttons.get("reset", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.reset_theme()
            return
        if self.settings_buttons.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay = None
            return

    def make_hue_surface(self, width: int, height: int) -> pygame.Surface:
        if self.hue_surface and self.hue_surface.get_size() == (width, height):
            return self.hue_surface

        surface = pygame.Surface((width, height))
        for x in range(width):
            hue = x / max(1, width - 1)
            red, green, blue = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = round(red * 255), round(green * 255), round(blue * 255)
            pygame.draw.line(surface, color, (x, 0), (x, height - 1))
        self.hue_surface = surface
        return surface

    def make_shade_surface(self, width: int, height: int) -> pygame.Surface:
        if (
            self.shade_surface
            and self.shade_surface.get_size() == (width, height)
            and abs(self.shade_surface_hue - self.picker_hue) < 0.0001
        ):
            return self.shade_surface

        surface = pygame.Surface((width, height))
        for x in range(width):
            saturation = x / max(1, width - 1)
            for y in range(height):
                value = 1.0 - y / max(1, height - 1)
                red, green, blue = colorsys.hsv_to_rgb(self.picker_hue, saturation, value)
                surface.set_at(
                    (x, y),
                    (round(red * 255), round(green * 255), round(blue * 255)),
                )

        self.shade_surface = surface
        self.shade_surface_hue = self.picker_hue
        return surface

    def draw_settings_overlay(self) -> None:
        shade = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))

        panel = self.theme_rgb["panel"]
        panel_alt = self.theme_rgb["panel_alt"]
        text = self.theme_rgb["text"]
        muted = self.theme_rgb["muted_text"]
        accent = self.theme_rgb["accent"]
        frame = self.theme_rgb["frame"]
        background = self.theme_rgb["background"]

        box = pygame.Rect(120, 58, 1120, 724)
        pygame.draw.rect(self.screen, panel, box, border_radius=10)
        pygame.draw.rect(self.screen, frame, box, 3, border_radius=10)

        dynamic_draw_text(self.screen, "Theme & Display Color Picker", box.x + 24, box.y + 18, self.font_title, text)
        dynamic_draw_text(
            self.screen,
            "Choose what to recolor, pick a hue, then click the shade you want.",
            box.x + 26,
            box.y + 58,
            self.font_small,
            muted,
        )

        self.theme_target_rects = []
        target_x = box.x + 26
        target_y = box.y + 96
        target_width = 355
        target_height = 42

        for index, (key, label) in enumerate(THEME_LABELS.items()):
            row = index
            rect = pygame.Rect(target_x, target_y + row * 45, target_width, target_height)
            selected = key == self.selected_theme_key
            pygame.draw.rect(self.screen, accent if selected else panel_alt, rect, border_radius=6)
            pygame.draw.rect(self.screen, frame if selected else self.theme_rgb["grid"], rect, 2, border_radius=6)

            swatch = pygame.Rect(rect.x + 8, rect.y + 7, 28, 28)
            color = hex_to_rgb(self.theme.get(key, "FFFFFF"), (255, 255, 255))
            pygame.draw.rect(self.screen, color, swatch, border_radius=4)
            pygame.draw.rect(self.screen, self.theme_rgb["item_stroke"], swatch, 2, border_radius=4)

            foreground = background if selected else text
            dynamic_draw_text(self.screen, label, rect.x + 46, rect.y + 11, self.font_small, foreground)
            self.theme_target_rects.append((key, rect))

        picker_x = box.x + 430
        picker_y = box.y + 104
        dynamic_draw_text(
            self.screen,
            f"Editing: {THEME_LABELS[self.selected_theme_key]}",
            picker_x,
            picker_y - 8,
            self.font_medium,
            text,
        )

        self.shade_rect = pygame.Rect(picker_x, picker_y + 34, 620, 390)
        shade_surface = self.make_shade_surface(self.shade_rect.width, self.shade_rect.height)
        self.screen.blit(shade_surface, self.shade_rect)
        pygame.draw.rect(self.screen, frame, self.shade_rect, 3)

        shade_marker_x = self.shade_rect.x + round(self.picker_saturation * (self.shade_rect.width - 1))
        shade_marker_y = self.shade_rect.y + round((1.0 - self.picker_value) * (self.shade_rect.height - 1))
        pygame.draw.circle(self.screen, (255, 255, 255), (shade_marker_x, shade_marker_y), 8, 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (shade_marker_x, shade_marker_y), 10, 2)

        self.hue_rect = pygame.Rect(picker_x, self.shade_rect.bottom + 24, 620, 32)
        self.screen.blit(self.make_hue_surface(self.hue_rect.width, self.hue_rect.height), self.hue_rect)
        pygame.draw.rect(self.screen, frame, self.hue_rect, 2)

        hue_marker_x = self.hue_rect.x + round(self.picker_hue * (self.hue_rect.width - 1))
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (hue_marker_x, self.hue_rect.y - 4),
            (hue_marker_x, self.hue_rect.bottom + 4),
            3,
        )
        pygame.draw.line(
            self.screen,
            (0, 0, 0),
            (hue_marker_x + 3, self.hue_rect.y - 4),
            (hue_marker_x + 3, self.hue_rect.bottom + 4),
            2,
        )

        preview_rect = pygame.Rect(picker_x, self.hue_rect.bottom + 24, 110, 58)
        pygame.draw.rect(self.screen, self.picker_rgb(), preview_rect, border_radius=7)
        pygame.draw.rect(self.screen, frame, preview_rect, 3, border_radius=7)
        dynamic_draw_text(self.screen, "Current color", preview_rect.right + 18, preview_rect.y + 17, self.font_medium, text)

        button_y = box.bottom - 58
        apply_rect = pygame.Rect(picker_x + 230, button_y, 170, 40)
        reset_rect = pygame.Rect(picker_x + 414, button_y, 160, 40)
        close_rect = pygame.Rect(box.right - 128, button_y, 100, 40)
        self.settings_buttons = {"apply": apply_rect, "reset": reset_rect, "close": close_rect}

        for name, rect, label in (
            ("apply", apply_rect, "Save Theme"),
            ("reset", reset_rect, "Reset Colors"),
            ("close", close_rect, "Close"),
        ):
            fill = accent if name == "apply" else panel_alt
            foreground = background if name == "apply" else text
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))
