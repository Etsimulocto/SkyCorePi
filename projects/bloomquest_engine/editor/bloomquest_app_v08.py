# bloomquest_app_v08.py
# run with: imported by bloomquest_v08.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v08.py
# description: Adds a dedicated Weapons panel and orbiting sword combat to BloomQuest.
# version: 0.8.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, sword, combat, editor, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, gamepad optional
# notes: Place a Sword in the Weapons panel to equip the player during Play Mode.
# uuid: bc-bloomquest-app-0008

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_RIGHT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    GRID_LINE,
    MUTED_TEXT,
    PANEL,
    PANEL_ALT,
    TEXT,
    TILE_SIZE,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v07 import BloomQuestAppV07
from engine.world_play_v08 import LAYER_ORDER_V08, WorldPlayV08

LAYER_LABELS_V08 = {
    "map": "Map",
    "scene_objects": "Scene Objects",
    "actors": "Enemies / Player",
    "weapons": "Weapons",
    "weapons_effects": "Effects",
}


class BloomQuestAppV08(BloomQuestAppV07):
    """BloomQuest v0.8 with a separate Weapons panel and orbit combat."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.8")
        self.room.setdefault("layers", {}).setdefault("weapons", [])
        self.status_message = "v0.8 ready. Place a Sword in Weapons to equip the player."

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.poll_gamepads()
            if self.mode == "play" and self.world_play and hasattr(self.world_play, "update"):
                self.world_play.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def visible_parts(self):
        return [
            (index, part)
            for index, part in enumerate(self.parts)
            if part.get("layer") == self.active_layer
        ]

    def set_layer(self, layer: str) -> None:
        self.room.setdefault("layers", {}).setdefault(layer, [])
        self.active_layer = layer
        self.clear_selection()
        for index, part in enumerate(self.parts):
            if part.get("layer") == layer:
                self.selected_part_index = index
                break
        self.status_message = f"Layer: {LAYER_LABELS_V08[layer]}"

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            x, y = event.pos
            button_x = 250
            for layer in LAYER_ORDER_V08:
                rect = pygame.Rect(button_x, 10, 128, 34)
                if rect.collidepoint(x, y):
                    self.set_layer(layer)
                    return
                button_x += 134

        super().handle_click(event)

    def find_at(self, gx: int, gy: int, layer: str | None = None):
        layers = [layer] if layer else list(reversed(LAYER_ORDER_V08))
        for current_layer in layers:
            for item in reversed(self.room.get("layers", {}).get(current_layer, [])):
                if item.get("x") == gx and item.get("y") == gy:
                    return item
        return None

    def draw_canvas(self) -> None:
        rect = pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, (20, 23, 28), rect)
        self.screen.set_clip(rect)
        start_x = self.camera_x // TILE_SIZE
        start_y = self.camera_y // TILE_SIZE

        for gy in range(start_y, start_y + CANVAS_HEIGHT // TILE_SIZE + 2):
            for gx in range(start_x, start_x + CANVAS_WIDTH // TILE_SIZE + 2):
                sx = CANVAS_LEFT + gx * TILE_SIZE - self.camera_x
                sy = CANVAS_TOP + gy * TILE_SIZE - self.camera_y
                pygame.draw.rect(self.screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

        for layer in LAYER_ORDER_V08:
            for item in self.room.get("layers", {}).get(layer, []):
                self.draw_item(self.screen, item, self.camera_x, self.camera_y, True)

        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, rect, 1)

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.8", 12, 5, self.font_large)
        draw_text(self.screen, self.current_room_id, 14, 32, self.font_small, MUTED_TEXT)

        if self.mode != "edit":
            return

        button_x = 250
        for layer in LAYER_ORDER_V08:
            rect = pygame.Rect(button_x, 10, 128, 34)
            active = layer == self.active_layer
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(
                LAYER_LABELS_V08[layer],
                True,
                BACKGROUND if active else TEXT,
            )
            self.screen.blit(image, image.get_rect(center=rect.center))
            button_x += 134

        for rect, label in (
            (self.rooms_button, "Rooms"),
            (self.help_button, "Help"),
            (self.play_button, "▶ Play"),
        ):
            is_play = label == "▶ Play"
            pygame.draw.rect(self.screen, ACCENT if is_play else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND if is_play else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def enter_play_mode(self) -> None:
        self.save_current_room()
        has_player = any(
            item.get("part_id") == "player"
            for item in self.room.get("layers", {}).get("actors", [])
        )
        if not has_player:
            self.status_message = "Place a Player in this room first."
            return

        self.world_play = WorldPlayV08(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.8 — PLAY MODE")

    def draw_play_mode(self) -> None:
        super().draw_play_mode()
        draw_text(self.screen, "Weapon behavior:", 18, TOP_BAR_HEIGHT + 334, self.font_small)
        draw_text(self.screen, "Placed Sword = equipped", 18, TOP_BAR_HEIGHT + 358, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Sword spins automatically", 18, TOP_BAR_HEIGHT + 382, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Hits damage nearby enemies", 18, TOP_BAR_HEIGHT + 406, self.font_small, MUTED_TEXT)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Equip the Sword",
                    "27. Open the Weapons panel.",
                    "28. Place one Sword anywhere in the room.",
                    "29. The placed Sword is equipment, not a pickup.",
                    "30. Enter Play Mode and it spins around the player automatically.",
                    "31. Move near enemies so the orbiting sword touches them.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Weapon Layer",
                    "A dedicated panel for equipment that belongs to the player during Play Mode.",
                    "## Orbit Weapon",
                    "A weapon that continuously travels around the player.",
                ]
            )
        else:
            content.extend(
                [
                    "## Weapons Panel",
                    "Weapons are separate from visual Effects.",
                    "Place a Sword anywhere in the room to equip it.",
                    "The Sword is not collected; it automatically orbits the player in Play Mode.",
                    "Sword contact reduces enemy health and defeated enemies add 1 score.",
                ]
            )

        return content
