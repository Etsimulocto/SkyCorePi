# world_play_v142.py
# run with: imported by editor/bloomquest_app_v142.py
# path: projects/bloomquest_engine/engine/world_play_v142.py
# description: Adds a complete Game Over restart that reloads the saved room and resets the whole play session.
# version: 0.14.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, game-over, restart, reset, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: R, Enter, Space, or gamepad A restarts after Game Over.
# uuid: bc-bloomquest-worldplay-0014-2

from __future__ import annotations

import pygame

from engine.world_play_v13 import WorldPlayV13


class WorldPlayV142(WorldPlayV13):
    """BloomQuest runtime with a full saved-state restart after defeat."""

    def __init__(self, room_manager, start_room_id: str, tile_size: int, canvas_rect: pygame.Rect) -> None:
        self._restart_room_manager = room_manager
        self._restart_room_id = start_room_id
        self._restart_tile_size = tile_size
        self._restart_canvas_rect = canvas_rect.copy()
        super().__init__(room_manager, start_room_id, tile_size, canvas_rect)

    @property
    def game_over(self) -> bool:
        return int(self.counters.get("health", 0)) <= 0

    def restart_game(self) -> None:
        """Rebuild the entire runtime from the room file saved by the editor."""
        room_manager = self._restart_room_manager
        room_id = self._restart_room_id
        tile_size = self._restart_tile_size
        canvas_rect = self._restart_canvas_rect.copy()
        self.__init__(room_manager, room_id, tile_size, canvas_rect)
        self.status = "Game restarted."
        self.message = ""

    def handle_key(self, event: pygame.event.Event) -> bool:
        if self.game_over:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in (
                pygame.K_r,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
            ):
                self.restart_game()
            return True

        return super().handle_key(event)

    def try_move(self, dx: int, dy: int) -> None:
        if self.game_over:
            return
        super().try_move(dx, dy)

    def interact(self) -> None:
        if self.game_over:
            self.restart_game()
            return
        super().interact()

    def fire_current_weapon(self) -> None:
        if self.game_over:
            return
        super().fire_current_weapon()

    def update(self) -> None:
        if self.game_over:
            self.message = "GAME OVER — Press R, Enter, Space, or gamepad A to restart"
            self.status = "Game Over — restart or press Esc to return to the editor."
            return
        super().update()
