# bloomquest_app_v11.py
# run with: imported by bloomquest_v11.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v11.py
# description: Adds Bow, Wand, Bombs, weapon switching, firing controls, and project weapon-library syncing.
# version: 0.11.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, bow, wand, bombs, gamepad, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, gamepad optional
# notes: Place weapons in the Weapons panel. Q/E or shoulders switch; Space or X fires.
# uuid: bc-bloomquest-app-0011

from __future__ import annotations

import json
from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    MUTED_TEXT,
    TILE_SIZE,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v103 import BloomQuestAppV103
from engine.world_play_v11 import WorldPlayV11


class BloomQuestAppV11(BloomQuestAppV103):
    """BloomQuest v0.11 with multiple selectable weapons."""

    REQUIRED_WEAPON_IDS = ("sword", "bow", "wand", "bomb")

    def __init__(self) -> None:
        super().__init__()
        self.sync_project_weapon_presets()
        pygame.display.set_caption("BloomQuest Engine v0.11 — Multi-Weapon")
        self.status_message = "Weapons ready: Sword, Bow, Wand, and Bombs."

    def sync_project_weapon_presets(self) -> None:
        """Add new engine weapon presets to older external projects once."""
        engine_parts_path = self.project_manager.engine_parts_file
        project_parts_path = self.project_manager.parts_file(self.project_id)

        with engine_parts_path.open("r", encoding="utf-8") as handle:
            engine_payload = json.load(handle)
        with project_parts_path.open("r", encoding="utf-8") as handle:
            project_payload = json.load(handle)

        existing_ids = {str(part.get("id", "")) for part in project_payload.get("parts", [])}
        added = 0
        for part in engine_payload.get("parts", []):
            if part.get("id") in self.REQUIRED_WEAPON_IDS and part.get("id") not in existing_ids:
                project_payload.setdefault("parts", []).append(deepcopy(part))
                existing_ids.add(part["id"])
                added += 1

        if added:
            with project_parts_path.open("w", encoding="utf-8") as handle:
                json.dump(project_payload, handle, indent=2, ensure_ascii=False)
            self.load_project_parts()

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        if hasattr(self, "project_manager"):
            self.sync_project_weapon_presets()

    def enter_play_mode(self) -> None:
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
        pygame.display.set_caption("BloomQuest Engine v0.11 — PLAY MODE")

    def handle_gamepad_button(self, button: int) -> None:
        if self.mode == "play" and self.world_play:
            if button == 0:
                self.world_play.interact()
            elif button == 2:
                self.world_play.fire_current_weapon()
            elif button == 4:
                self.world_play.cycle_weapon(-1)
            elif button == 5:
                self.world_play.cycle_weapon(1)
            elif button in (1, 6, 7):
                self.exit_play_mode()
            return
        super().handle_gamepad_button(button)

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        pygame.draw.rect(self.screen, (35, 39, 47), (0, 0, 205, TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.11", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

    def draw_play_mode(self) -> None:
        super().draw_play_mode()
        draw_text(self.screen, "Multi-weapon:", 18, TOP_BAR_HEIGHT + 574, self.font_small)
        draw_text(self.screen, "Q / E = switch", 18, TOP_BAR_HEIGHT + 598, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Space = fire / drop", 18, TOP_BAR_HEIGHT + 622, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Gamepad: LB/RB + X", 18, TOP_BAR_HEIGHT + 646, self.font_small, MUTED_TEXT)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend([
                "## Multiple Weapons",
                "43. Open Weapons and place Sword, Bow, Wand, or Bombs.",
                "44. Every placed weapon becomes available in Play Mode.",
                "45. Press Q/E or LB/RB to switch weapons.",
                "46. Press Space or gamepad X to fire or drop the selected weapon.",
            ])
        elif page == "glossary":
            content.extend([
                "## Projectile", "A moving attack such as an arrow or magic bolt.",
                "## Cooldown", "The short wait before a weapon can fire again.",
                "## Fuse", "The delay before a placed bomb activates.",
            ])
        else:
            content.extend([
                "## Weapon Types",
                "Sword: automatically orbits while selected.",
                "Bow: fires fast arrows in the facing direction.",
                "Wand: fires stronger magic bolts.",
                "Bombs: remain on the current tile, then affect nearby enemies.",
            ])
        return content
