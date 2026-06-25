# bloomquest_app_v18.py
# run with: imported by bloomquest_v18.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v18.py
# description: Adds touch-to-reveal fog-of-war controls to the BloomQuest Overlay menu.
# version: 0.18.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, fog-of-war, exploration, overlay, editor, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Exploration fog settings save inside project.json.
# uuid: bc-bloomquest-app-0018

from __future__ import annotations

from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    TILE_SIZE,
)
from editor.bloomquest_app_v14 import dynamic_draw_text
from editor.bloomquest_app_v171 import BloomQuestAppV171
from engine.world_play_v18 import WorldPlayV18


class BloomQuestAppV18(BloomQuestAppV171):
    """BloomQuest v0.18 with touch-to-reveal exploration fog."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.18 — Exploration Fog")
        self.status_message = "Exploration Fog ready: tiles reveal as the player touches them."

    def default_overlay_config(self) -> dict:
        config = super().default_overlay_config()
        config.update(
            {
                "exploration_fog": False,
                "exploration_radius": 0,
                "exploration_opacity": 255,
                "exploration_color": [0, 0, 0],
            }
        )
        return config

    def handle_overlay_settings_click(self, position: tuple[int, int]) -> None:
        fog_toggle = self.overlay_control_rects.get("exploration_fog", pygame.Rect(0, 0, 0, 0))
        if fog_toggle.collidepoint(position):
            self.overlay_config["exploration_fog"] = not bool(self.overlay_config.get("exploration_fog", False))
            return

        adjustments = {
            "explore_radius_minus": ("exploration_radius", -1, 0, 6),
            "explore_radius_plus": ("exploration_radius", 1, 0, 6),
            "explore_opacity_minus": ("exploration_opacity", -15, 0, 255),
            "explore_opacity_plus": ("exploration_opacity", 15, 0, 255),
        }
        for name, args in adjustments.items():
            rect = self.overlay_control_rects.get(name, pygame.Rect(0, 0, 0, 0))
            if rect.collidepoint(position):
                self.adjust_overlay_value(*args)
                return

        super().handle_overlay_settings_click(position)

    def draw_overlay_settings(self) -> None:
        super().draw_overlay_settings()

        box = pygame.Rect(130, 62, 1100, 716)
        section = pygame.Rect(box.x + 24, box.y + 446, 640, 194)
        pygame.draw.rect(self.screen, self.theme_rgb["panel_alt"], section, border_radius=8)
        pygame.draw.rect(self.screen, self.theme_rgb["grid"], section, 2, border_radius=8)

        dynamic_draw_text(
            self.screen,
            "Exploration Fog",
            section.x + 16,
            section.y + 12,
            self.font_medium,
            self.theme_rgb["text"],
        )
        dynamic_draw_text(
            self.screen,
            "Black out every undiscovered tile until the player reaches it.",
            section.x + 16,
            section.y + 40,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        enabled = bool(self.overlay_config.get("exploration_fog", False))
        toggle = pygame.Rect(section.x + 16, section.y + 72, 220, 38)
        pygame.draw.rect(
            self.screen,
            self.theme_rgb["accent"] if enabled else self.theme_rgb["field"],
            toggle,
            border_radius=6,
        )
        toggle_text = "✓ Exploration Fog On" if enabled else "○ Exploration Fog Off"
        toggle_color = self.theme_rgb["background"] if enabled else self.theme_rgb["text"]
        image = self.font_small.render(toggle_text, True, toggle_color)
        self.screen.blit(image, image.get_rect(center=toggle.center))
        self.overlay_control_rects["exploration_fog"] = toggle

        self.draw_exploration_stepper(
            section.x + 258,
            section.y + 70,
            "Reveal Radius",
            int(self.overlay_config.get("exploration_radius", 0)),
            "explore_radius",
        )
        self.draw_exploration_stepper(
            section.x + 258,
            section.y + 126,
            "Fog Opacity",
            int(self.overlay_config.get("exploration_opacity", 255)),
            "explore_opacity",
        )

        dynamic_draw_text(
            self.screen,
            "Radius 0 reveals only the tile touched. Radius 1 reveals adjacent tiles too.",
            section.x + 16,
            section.bottom - 28,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

    def draw_exploration_stepper(self, x: int, y: int, label: str, value: int, key: str) -> None:
        dynamic_draw_text(self.screen, label, x, y - 2, self.font_small, self.theme_rgb["text"])

        minus = pygame.Rect(x + 170, y - 7, 38, 34)
        value_rect = pygame.Rect(x + 216, y - 7, 88, 34)
        plus = pygame.Rect(x + 312, y - 7, 38, 34)

        for rect, symbol in ((minus, "−"), (plus, "+")):
            pygame.draw.rect(self.screen, self.theme_rgb["field"], rect, border_radius=5)
            image = self.font_small.render(symbol, True, self.theme_rgb["text"])
            self.screen.blit(image, image.get_rect(center=rect.center))

        pygame.draw.rect(self.screen, self.theme_rgb["field"], value_rect, border_radius=5)
        value_image = self.font_small.render(str(value), True, self.theme_rgb["text"])
        self.screen.blit(value_image, value_image.get_rect(center=value_rect.center))

        self.overlay_control_rects[f"{key}_minus"] = minus
        self.overlay_control_rects[f"{key}_plus"] = plus

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

        self.world_play = WorldPlayV18(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
            game_config=deepcopy(self.game_config),
            overlay_config=overlay_config,
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.18 — PLAY MODE")

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend(
                [
                    "## Exploration Fog",
                    "71. Open Overlay and turn Exploration Fog on.",
                    "72. Set Reveal Radius to 0 to reveal only tiles the player touches.",
                    "73. Increase Reveal Radius to reveal nearby tiles while walking.",
                    "74. Adjust Fog Opacity from transparent to completely black.",
                    "75. Revealed tiles remain visible until the play session is restarted.",
                ]
            )
        else:
            content.extend(
                [
                    "## Touch-to-Reveal Map",
                    "Exploration Fog hides map tiles, objects, enemies, and treasure until discovered.",
                    "Each room remembers its own revealed tiles during the current play session.",
                ]
            )
        return content
