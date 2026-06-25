# world_play_v16.py
# run with: imported by editor/bloomquest_app_v16.py
# path: projects/bloomquest_engine/engine/world_play_v16.py
# description: Adds title screen, pause menu, configurable objectives, win detection, and victory screen.
# version: 0.16.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, title-screen, pause, objectives, victory, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Enter/Space/A starts. Esc/P pauses. Q exits from pause.
# uuid: bc-bloomquest-worldplay-0016

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pygame

from engine.world_play_v142 import WorldPlayV142


class WorldPlayV16(WorldPlayV142):
    """Complete play loop with title, objective, pause, victory, and restart states."""

    def __init__(
        self,
        room_manager,
        start_room_id: str,
        tile_size: int,
        canvas_rect: pygame.Rect,
        game_config: dict[str, Any] | None = None,
    ) -> None:
        self.game_config = deepcopy(game_config or {})
        super().__init__(room_manager, start_room_id, tile_size, canvas_rect)

        self.state = "title"
        self.exit_reached = False
        self.started_at_ms = 0
        self.elapsed_seconds = 0
        self.title_font = pygame.font.SysFont("Segoe UI", 44, bold=True)
        self.subtitle_font = pygame.font.SysFont("Segoe UI", 22)
        self.menu_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.status = "Press Enter, Space, or gamepad A to begin."

    @property
    def title(self) -> str:
        return str(self.game_config.get("title") or "BloomQuest Adventure")

    @property
    def subtitle(self) -> str:
        return str(self.game_config.get("subtitle") or "A tiny generated adventure")

    @property
    def objective_type(self) -> str:
        return str(self.game_config.get("objective", "defeat_all"))

    @property
    def objective_target(self) -> int:
        try:
            return max(1, int(self.game_config.get("target", 5)))
        except (TypeError, ValueError):
            return 5

    def objective_text(self) -> str:
        labels = {
            "defeat_all": "Defeat every enemy",
            "collect_coins": f"Collect {self.objective_target} coins",
            "collect_keys": f"Collect {self.objective_target} keys",
            "reach_exit": "Reach the exit door",
            "score": f"Earn {self.objective_target} score",
            "survive_timer": f"Survive {self.objective_target} seconds",
        }
        return labels.get(self.objective_type, "Defeat every enemy")

    def start_game(self) -> None:
        self.state = "playing"
        self.started_at_ms = pygame.time.get_ticks()
        self.elapsed_seconds = 0
        self.message = ""
        self.status = f"Objective: {self.objective_text()}"

    def restart_game(self) -> None:
        """Rebuild the whole saved session, then immediately begin playing."""
        room_manager = self._restart_room_manager
        room_id = self._restart_room_id
        tile_size = self._restart_tile_size
        canvas_rect = self._restart_canvas_rect.copy()
        config = deepcopy(self.game_config)
        self.__init__(room_manager, room_id, tile_size, canvas_rect, config)
        self.start_game()
        self.status = "Adventure restarted."

    def return_to_title(self) -> None:
        room_manager = self._restart_room_manager
        room_id = self._restart_room_id
        tile_size = self._restart_tile_size
        canvas_rect = self._restart_canvas_rect.copy()
        config = deepcopy(self.game_config)
        self.__init__(room_manager, room_id, tile_size, canvas_rect, config)

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
            self.status = "Paused."
        elif self.state == "paused":
            pause_duration = pygame.time.get_ticks() - self.started_at_ms - self.elapsed_seconds * 1000
            self.started_at_ms += max(0, pause_duration)
            self.state = "playing"
            self.status = f"Objective: {self.objective_text()}"

    def handle_key(self, event: pygame.event.Event) -> bool:
        if self.state == "title":
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            return True

        if self.state == "won":
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_r):
                self.restart_game()
            elif event.key == pygame.K_t:
                self.return_to_title()
            return True

        if self.game_over:
            return super().handle_key(event)

        if self.state == "paused":
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.toggle_pause()
            elif event.key == pygame.K_r:
                self.restart_game()
            elif event.key == pygame.K_t:
                self.return_to_title()
            elif event.key == pygame.K_q:
                return False
            return True

        if event.key in (pygame.K_ESCAPE, pygame.K_p):
            self.toggle_pause()
            return True

        return super().handle_key(event)

    def interact(self) -> None:
        if self.state == "title":
            self.start_game()
            return
        if self.state in ("paused", "won"):
            return
        super().interact()

    def try_move(self, dx: int, dy: int) -> None:
        if self.state != "playing":
            return
        super().try_move(dx, dy)

    def fire_current_weapon(self) -> None:
        if self.state != "playing":
            return
        super().fire_current_weapon()

    def execute(self, item: dict[str, Any], action: dict[str, Any]) -> None:
        if item.get("part_id") == "door":
            self.exit_reached = True
        super().execute(item, action)

    def objective_complete(self) -> bool:
        objective = self.objective_type
        if objective == "defeat_all":
            return len(self.enemy_items()) == 0
        if objective == "collect_coins":
            return int(self.counters.get("coins", 0)) >= self.objective_target
        if objective == "collect_keys":
            return int(self.counters.get("keys", 0)) >= self.objective_target
        if objective == "reach_exit":
            return self.exit_reached
        if objective == "score":
            return int(self.counters.get("score", 0)) >= self.objective_target
        if objective == "survive_timer":
            return self.elapsed_seconds >= self.objective_target
        return len(self.enemy_items()) == 0

    def update(self) -> None:
        if self.state != "playing":
            return

        super().update()
        if self.game_over:
            return

        self.elapsed_seconds = max(0, (pygame.time.get_ticks() - self.started_at_ms) // 1000)
        self.counters["timer"] = self.elapsed_seconds

        if self.objective_complete():
            self.state = "won"
            self.message = ""
            self.status = "Objective complete — You Win!"

    def draw(
        self,
        surface: pygame.Surface,
        draw_item: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None],
        colors: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        super().draw(surface, draw_item, colors, fonts)

        if self.state == "title":
            self.draw_title_screen(surface, colors)
        elif self.state == "paused":
            self.draw_pause_screen(surface, colors)
        elif self.state == "won":
            self.draw_win_screen(surface, colors)

    def overlay_panel(self, surface: pygame.Surface, colors, width: int, height: int) -> pygame.Rect:
        shade = pygame.Surface((self.canvas_rect.width, self.canvas_rect.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        surface.blit(shade, self.canvas_rect.topleft)
        rect = pygame.Rect(0, 0, width, height)
        rect.center = self.canvas_rect.center
        pygame.draw.rect(surface, colors["panel"], rect, border_radius=12)
        pygame.draw.rect(surface, colors["accent"], rect, 3, border_radius=12)
        return rect

    def draw_title_screen(self, surface: pygame.Surface, colors) -> None:
        rect = self.overlay_panel(surface, colors, 620, 330)
        title_image = self.title_font.render(self.title, True, colors["text"])
        surface.blit(title_image, title_image.get_rect(center=(rect.centerx, rect.y + 76)))

        subtitle_image = self.subtitle_font.render(self.subtitle, True, colors["text"])
        surface.blit(subtitle_image, subtitle_image.get_rect(center=(rect.centerx, rect.y + 126)))

        objective_image = self.subtitle_font.render(f"Objective: {self.objective_text()}", True, colors["accent"])
        surface.blit(objective_image, objective_image.get_rect(center=(rect.centerx, rect.y + 188)))

        start_image = self.menu_font.render("Press Enter / Space / A to Start", True, colors["text"])
        surface.blit(start_image, start_image.get_rect(center=(rect.centerx, rect.y + 254)))

    def draw_pause_screen(self, surface: pygame.Surface, colors) -> None:
        rect = self.overlay_panel(surface, colors, 500, 300)
        title_image = self.title_font.render("PAUSED", True, colors["text"])
        surface.blit(title_image, title_image.get_rect(center=(rect.centerx, rect.y + 62)))

        lines = (
            "Esc / P — Resume",
            "R — Restart Adventure",
            "T — Return to Title",
            "Q — Return to Editor",
        )
        for index, line in enumerate(lines):
            image = self.subtitle_font.render(line, True, colors["text"])
            surface.blit(image, image.get_rect(center=(rect.centerx, rect.y + 128 + index * 38)))

    def draw_win_screen(self, surface: pygame.Surface, colors) -> None:
        rect = self.overlay_panel(surface, colors, 600, 330)
        title_image = self.title_font.render("YOU WIN!", True, colors["accent"])
        surface.blit(title_image, title_image.get_rect(center=(rect.centerx, rect.y + 72)))

        objective_image = self.subtitle_font.render(self.objective_text(), True, colors["text"])
        surface.blit(objective_image, objective_image.get_rect(center=(rect.centerx, rect.y + 132)))

        score_image = self.subtitle_font.render(
            f"Score: {self.counters.get('score', 0)}   Time: {self.elapsed_seconds}s",
            True,
            colors["text"],
        )
        surface.blit(score_image, score_image.get_rect(center=(rect.centerx, rect.y + 184)))

        restart_image = self.menu_font.render("Enter / Space / R — Play Again", True, colors["text"])
        surface.blit(restart_image, restart_image.get_rect(center=(rect.centerx, rect.y + 244)))

        title_hint = self.subtitle_font.render("T — Title Screen   Esc — Editor", True, colors["text"])
        surface.blit(title_hint, title_hint.get_rect(center=(rect.centerx, rect.y + 286)))
