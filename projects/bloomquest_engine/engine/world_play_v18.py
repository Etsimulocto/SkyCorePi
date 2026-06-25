# world_play_v18.py
# run with: imported by editor/bloomquest_app_v18.py
# path: projects/bloomquest_engine/engine/world_play_v18.py
# description: Adds tile-based fog of war that reveals map tiles as the player explores them.
# version: 0.18.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, fog-of-war, exploration, reveal, map, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Revealed tiles persist for the current play session and reset with a full restart.
# uuid: bc-bloomquest-worldplay-0018

from __future__ import annotations

from typing import Any, Callable

import pygame

from engine.world_play_v17 import WorldPlayV17


class WorldPlayV18(WorldPlayV17):
    """BloomQuest runtime with touch-to-reveal exploration fog."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.revealed_tiles: dict[str, set[tuple[int, int]]] = {}
        self.reveal_current_area()

    @property
    def exploration_enabled(self) -> bool:
        return bool(self.overlay_config.get("exploration_fog", False))

    @property
    def exploration_radius(self) -> int:
        try:
            return max(0, min(6, int(self.overlay_config.get("exploration_radius", 0))))
        except (TypeError, ValueError):
            return 0

    def room_revealed_tiles(self) -> set[tuple[int, int]]:
        return self.revealed_tiles.setdefault(self.room_id, set())

    def reveal_current_area(self) -> None:
        revealed = self.room_revealed_tiles()
        radius = self.exploration_radius

        for offset_y in range(-radius, radius + 1):
            for offset_x in range(-radius, radius + 1):
                if abs(offset_x) + abs(offset_y) <= radius:
                    revealed.add((self.player_x + offset_x, self.player_y + offset_y))

        revealed.add((self.player_x, self.player_y))

    def try_move(self, dx: int, dy: int) -> None:
        old_position = (self.player_x, self.player_y)
        super().try_move(dx, dy)
        if (self.player_x, self.player_y) != old_position:
            self.reveal_current_area()

    def change_room(self, room_id: str, x: int, y: int) -> None:
        super().change_room(room_id, x, y)
        self.reveal_current_area()

    def draw(
        self,
        surface: pygame.Surface,
        draw_item: Callable[[pygame.Surface, dict[str, Any], int, int, bool], None],
        colors: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        super().draw(surface, draw_item, colors, fonts)

        if self.exploration_enabled and self.state == "playing" and not self.game_over:
            self.draw_exploration_fog(surface)
            self.redraw_hud(surface, colors, fonts)

    def draw_exploration_fog(self, surface: pygame.Surface) -> None:
        revealed = self.room_revealed_tiles()
        fog_alpha = max(0, min(255, int(self.overlay_config.get("exploration_opacity", 255))))
        fog_color = tuple(self.overlay_config.get("exploration_color", [0, 0, 0]))

        grid = self.room.get("grid", {})
        columns = int(grid.get("columns", 128))
        rows = int(grid.get("rows", 128))

        start_x = max(0, self.camera_x // self.tile_size)
        start_y = max(0, self.camera_y // self.tile_size)
        visible_columns = self.canvas_rect.width // self.tile_size + 2
        visible_rows = self.canvas_rect.height // self.tile_size + 2

        fog_surface = pygame.Surface(self.canvas_rect.size, pygame.SRCALPHA)

        for tile_y in range(start_y, min(rows, start_y + visible_rows)):
            for tile_x in range(start_x, min(columns, start_x + visible_columns)):
                if (tile_x, tile_y) in revealed:
                    continue

                screen_x = tile_x * self.tile_size - self.camera_x
                screen_y = tile_y * self.tile_size - self.camera_y
                pygame.draw.rect(
                    fog_surface,
                    (*fog_color, fog_alpha),
                    (screen_x, screen_y, self.tile_size, self.tile_size),
                )

        surface.blit(fog_surface, self.canvas_rect.topleft)

    def redraw_hud(
        self,
        surface: pygame.Surface,
        colors: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        """Keep the HUD readable after the fog layer covers undiscovered tiles."""
        hud = pygame.Rect(self.canvas_rect.x + 10, self.canvas_rect.y + 10, 690, 38)
        pygame.draw.rect(surface, colors["panel"], hud, border_radius=7)

        weapon = self.current_weapon()
        weapon_label = weapon.get("emoji", "") + " " + weapon.get("name", "Weapon") if weapon else "No weapon"
        label = (
            f"{self.room_id}   ❤️ {self.counters.get('health', 0)}   "
            f"🪙 {self.counters.get('coins', 0)}   ⭐ {self.counters.get('score', 0)}   "
            f"🗝️ {self.counters.get('keys', 0)}   {weapon_label}"
        )
        image = fonts["medium"].render(label, True, colors["text"])
        surface.blit(image, image.get_rect(midleft=(hud.x + 12, hud.centery)))

        if self.message:
            box = pygame.Rect(
                self.canvas_rect.x + 40,
                self.canvas_rect.bottom - 110,
                self.canvas_rect.width - 80,
                72,
            )
            pygame.draw.rect(surface, colors["panel"], box, border_radius=8)
            pygame.draw.rect(surface, colors["accent"], box, 2, border_radius=8)
            message_image = fonts["medium"].render(self.message[:90], True, colors["text"])
            surface.blit(message_image, (box.x + 14, box.y + 22))
