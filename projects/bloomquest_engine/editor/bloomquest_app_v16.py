# bloomquest_app_v16.py
# run with: imported by bloomquest_v16.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v16.py
# description: Adds project game settings for title, subtitle, objectives, targets, pause, and victory flow.
# version: 0.16.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, game-settings, title-screen, objectives, pause, victory, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Game settings save inside project.json.
# uuid: bc-bloomquest-app-0016

from __future__ import annotations

from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    BACKGROUND,
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    MUTED_TEXT,
    PANEL_ALT,
    TEXT,
    TILE_SIZE,
    TOP_BAR_HEIGHT,
    TextField,
)
from editor.bloomquest_app_v14 import dynamic_draw_text
from editor.bloomquest_app_v15 import BloomQuestAppV15
from engine.world_play_v16 import WorldPlayV16


class BloomQuestAppV16(BloomQuestAppV15):
    """BloomQuest v0.16 with complete project game-loop settings."""

    OBJECTIVES = {
        "defeat_all": ("Defeat All", "Win when every enemy is defeated."),
        "collect_coins": ("Collect Coins", "Win after collecting the target number of coins."),
        "collect_keys": ("Collect Keys", "Win after collecting the target number of keys."),
        "reach_exit": ("Reach Exit", "Win by touching a door."),
        "score": ("Reach Score", "Win after earning the target score."),
        "survive_timer": ("Survive Timer", "Win after surviving the target number of seconds."),
    }

    def __init__(self) -> None:
        super().__init__()

        self.project_button = pygame.Rect(820, 10, 76, 34)
        self.rooms_button = pygame.Rect(902, 10, 68, 34)
        self.game_button = pygame.Rect(976, 10, 68, 34)
        self.maps_button = pygame.Rect(1050, 10, 68, 34)
        self.settings_button = pygame.Rect(1124, 10, 84, 34)
        self.help_button = pygame.Rect(1214, 10, 62, 34)
        self.play_button = pygame.Rect(1282, 10, 72, 34)

        self.game_fields: list[TextField] = []
        self.game_buttons: dict[str, pygame.Rect] = {}
        self.objective_rects: list[tuple[str, pygame.Rect]] = []
        self.game_config = self.default_game_config()
        self.load_game_config()

        pygame.display.set_caption("BloomQuest Engine v0.16 — Complete Game Loop")
        self.status_message = "Game menu ready: title, objectives, pause, and victory."

    def default_game_config(self) -> dict:
        return {
            "title": self.project.get("name", "BloomQuest Adventure") if hasattr(self, "project") else "BloomQuest Adventure",
            "subtitle": "A tiny BloomQuest adventure",
            "objective": "defeat_all",
            "target": 5,
        }

    def load_game_config(self) -> None:
        saved = self.project.get("game", {}) if hasattr(self, "project") else {}
        config = self.default_game_config()
        config.update(saved)
        if config.get("objective") not in self.OBJECTIVES:
            config["objective"] = "defeat_all"
        try:
            config["target"] = max(1, int(config.get("target", 5)))
        except (TypeError, ValueError):
            config["target"] = 5
        self.game_config = config

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        self.load_game_config()

    def build_game_fields(self) -> None:
        self.game_fields = [
            TextField("game_title", "Game Title", self.game_config.get("title", "BloomQuest Adventure")),
            TextField("game_subtitle", "Subtitle", self.game_config.get("subtitle", "A tiny BloomQuest adventure")),
            TextField("game_target", "Objective Target", self.game_config.get("target", 5), numeric=True),
        ]

    def active_text_field(self):
        if self.overlay == "game_settings":
            return next((field for field in self.game_fields if field.active), None)
        return super().active_text_field()

    def save_game_config(self) -> None:
        values = {field.key: field.value for field in self.game_fields}
        self.game_config["title"] = values.get("game_title", "").strip() or "BloomQuest Adventure"
        self.game_config["subtitle"] = values.get("game_subtitle", "").strip() or "A tiny BloomQuest adventure"
        try:
            self.game_config["target"] = max(1, int(values.get("game_target", 5)))
        except (TypeError, ValueError):
            self.game_config["target"] = 5

        self.project["game"] = deepcopy(self.game_config)
        self.project_manager.save_project(self.project)
        self.status_message = "Game settings saved to this project."

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.overlay == "game_settings":
            self.handle_game_settings_click(event.pos)
            return

        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            position = event.pos
            if self.game_button.collidepoint(position):
                self.build_game_fields()
                self.overlay = "game_settings"
                return

        super().handle_click(event)

    def handle_game_settings_click(self, position: tuple[int, int]) -> None:
        for field in self.game_fields:
            field.active = field.rect.collidepoint(position)

        for objective, rect in self.objective_rects:
            if rect.collidepoint(position):
                self.game_config["objective"] = objective
                self.status_message = f"Objective: {self.OBJECTIVES[objective][0]}"
                return

        if self.game_buttons.get("save", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.save_game_config()
            return
        if self.game_buttons.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
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

    def draw_overlay(self) -> None:
        if self.overlay != "game_settings":
            super().draw_overlay()
            return
        self.draw_game_settings_overlay()

    def draw_game_settings_overlay(self) -> None:
        shade = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))

        box = pygame.Rect(170, 70, 1020, 690)
        pygame.draw.rect(self.screen, self.theme_rgb["panel"], box, border_radius=10)
        pygame.draw.rect(self.screen, self.theme_rgb["frame"], box, 3, border_radius=10)

        dynamic_draw_text(self.screen, "Game Settings", box.x + 24, box.y + 18, self.font_title, self.theme_rgb["text"])
        dynamic_draw_text(
            self.screen,
            "Build the title screen and choose how the player wins.",
            box.x + 26,
            box.y + 60,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        y = box.y + 102
        for field in self.game_fields:
            dynamic_draw_text(self.screen, field.label, box.x + 28, y, self.font_small, self.theme_rgb["muted_text"])
            y += 22
            field.rect = pygame.Rect(box.x + 28, y, 440, 40)
            pygame.draw.rect(self.screen, self.theme_rgb["field"], field.rect, border_radius=6)
            pygame.draw.rect(
                self.screen,
                self.theme_rgb["accent"] if field.active else self.theme_rgb["grid"],
                field.rect,
                2,
                border_radius=6,
            )
            dynamic_draw_text(self.screen, field.value[-80:], field.rect.x + 10, field.rect.y + 10, self.font_small, self.theme_rgb["text"])
            y += 58

        dynamic_draw_text(self.screen, "Win Objective", box.x + 510, box.y + 104, self.font_medium, self.theme_rgb["text"])
        self.objective_rects = []
        objective_y = box.y + 142

        for index, (objective, (title, description)) in enumerate(self.OBJECTIVES.items()):
            rect = pygame.Rect(box.x + 510, objective_y + index * 74, 476, 64)
            selected = objective == self.game_config.get("objective")
            pygame.draw.rect(
                self.screen,
                self.theme_rgb["accent"] if selected else self.theme_rgb["panel_alt"],
                rect,
                border_radius=7,
            )
            pygame.draw.rect(
                self.screen,
                self.theme_rgb["frame"] if selected else self.theme_rgb["grid"],
                rect,
                2,
                border_radius=7,
            )
            foreground = self.theme_rgb["background"] if selected else self.theme_rgb["text"]
            secondary = self.theme_rgb["background"] if selected else self.theme_rgb["muted_text"]
            dynamic_draw_text(self.screen, title, rect.x + 14, rect.y + 9, self.font_medium, foreground)
            dynamic_draw_text(self.screen, description, rect.x + 14, rect.y + 37, self.font_small, secondary)
            self.objective_rects.append((objective, rect))

        note_y = box.bottom - 112
        dynamic_draw_text(
            self.screen,
            "Pause: Esc or P   |   Restart: R   |   Title: T   |   Editor: Q from pause",
            box.x + 28,
            note_y,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        save_rect = pygame.Rect(box.x + 28, box.bottom - 62, 180, 40)
        close_rect = pygame.Rect(box.right - 128, box.bottom - 62, 100, 40)
        self.game_buttons = {"save": save_rect, "close": close_rect}

        pygame.draw.rect(self.screen, self.theme_rgb["accent"], save_rect, border_radius=6)
        image = self.font_small.render("Save Game Settings", True, self.theme_rgb["background"])
        self.screen.blit(image, image.get_rect(center=save_rect.center))

        pygame.draw.rect(self.screen, self.theme_rgb["panel_alt"], close_rect, border_radius=6)
        image = self.font_small.render("Close", True, self.theme_rgb["text"])
        self.screen.blit(image, image.get_rect(center=close_rect.center))

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

        self.world_play = WorldPlayV16(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
            deepcopy(self.game_config),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.16 — PLAY MODE")

    def handle_gamepad_button(self, button: int) -> None:
        if self.mode == "play" and self.world_play:
            state = getattr(self.world_play, "state", "playing")

            if state == "title":
                if button == 0:
                    self.world_play.start_game()
                elif button in (1, 6):
                    self.exit_play_mode()
                return

            if state == "won":
                if button == 0:
                    self.world_play.restart_game()
                elif button in (1, 6):
                    self.exit_play_mode()
                return

            if getattr(self.world_play, "game_over", False):
                if button == 0:
                    self.world_play.restart_game()
                elif button in (1, 6):
                    self.exit_play_mode()
                return

            if button == 7:
                self.world_play.toggle_pause()
                return
            if state == "paused":
                if button == 0:
                    self.world_play.toggle_pause()
                elif button == 1:
                    self.exit_play_mode()
                return

        super().handle_gamepad_button(button)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend([
                "## Complete the Game Loop",
                "60. Open Game from the top bar.",
                "61. Enter a game title and subtitle.",
                "62. Choose a win objective and set its target.",
                "63. Save Game Settings and enter Play Mode.",
                "64. The title screen appears before gameplay.",
                "65. Complete the objective to open the You Win screen.",
            ])
        else:
            content.extend([
                "## Title, Pause, and Victory",
                "Projects can define their own title, subtitle, objective, and target.",
                "Esc or P pauses. R restarts. T returns to the title. Q returns to the editor from pause.",
            ])
        return content
