from __future__ import annotations

import pygame

from editor.bloomquest_app import CANVAS_HEIGHT, CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, TILE_SIZE
from editor.bloomquest_app_v11 import BloomQuestAppV11
from editor.equipment_patch_v112 import EquipmentPatchV112
from engine.world_play_v11 import WorldPlayV11


class BloomQuestAppV112(EquipmentPatchV112, BloomQuestAppV11):
    def __init__(self) -> None:
        super().__init__()
        self.repair_equipment()
        pygame.display.set_caption("BloomQuest Engine v0.11.2")
        self.status_message = "Equipment metadata repaired."

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        if hasattr(self, "room"):
            self.repair_equipment()

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

        self.world_play = WorldPlayV11(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.11.2 — PLAY MODE")
