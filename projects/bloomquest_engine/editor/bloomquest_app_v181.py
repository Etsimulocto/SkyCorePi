# bloomquest_app_v181.py
# run with: imported by bloomquest_v181.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v181.py
# description: Launches Play Mode with the BloomQuest Adventure 001 cover title screen.
# version: 0.18.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, cover, title-screen, editor, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: The cover is loaded automatically from assets, project assets, Downloads, or Desktop.
# uuid: bc-bloomquest-app-0018-1

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
from editor.bloomquest_app_v18 import BloomQuestAppV18
from engine.world_play_v181 import WorldPlayV181


class BloomQuestAppV181(BloomQuestAppV18):
    """BloomQuest v0.18.1 with illustrated cover art in Play Mode."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.18.1 — Cover Edition")
        self.status_message = "Cover Edition ready. Download the cover PNG and Play Mode will find it automatically."

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

        self.world_play = WorldPlayV181(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
            game_config=deepcopy(self.game_config),
            overlay_config=overlay_config,
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.18.1 — PLAY MODE")
