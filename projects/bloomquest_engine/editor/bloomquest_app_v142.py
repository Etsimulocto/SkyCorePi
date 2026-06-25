# bloomquest_app_v142.py
# run with: imported by bloomquest_v142.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v142.py
# description: Uses the complete Game Over restart runtime with the visual theme editor.
# version: 0.14.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, game-over, restart, theme, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Gamepad A restarts after Game Over.
# uuid: bc-bloomquest-app-0014-2

from __future__ import annotations

import pygame

from editor.bloomquest_app import CANVAS_HEIGHT, CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, TILE_SIZE
from editor.bloomquest_app_v141 import BloomQuestAppV141
from engine.world_play_v142 import WorldPlayV142


class BloomQuestAppV142(BloomQuestAppV141):
    """BloomQuest v0.14.2 with a complete restartable Game Over state."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.14.2 — Restartable Game Over")
        self.status_message = "Game Over now supports a full restart."

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

        self.world_play = WorldPlayV142(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.14.2 — PLAY MODE")

    def handle_gamepad_button(self, button: int) -> None:
        if self.mode == "play" and self.world_play:
            if getattr(self.world_play, "game_over", False):
                if button == 0:
                    self.world_play.restart_game()
                elif button in (1, 6, 7):
                    self.exit_play_mode()
                return

        super().handle_gamepad_button(button)
