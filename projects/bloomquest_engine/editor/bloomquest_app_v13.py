# bloomquest_app_v13.py
# run with: imported by bloomquest_v13.py
# description: Adds a Decorations layer, animated map accents, and room atmosphere markers.

from __future__ import annotations

import json
from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    ACCENT,
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
    draw_text,
)
from editor.bloomquest_app_v12 import BloomQuestAppV12
from engine.world_play_v13 import WorldPlayV13


class BloomQuestAppV13(BloomQuestAppV12):
    DECORATION_IDS = (
        "flower",
        "mushroom",
        "grass_tuft",
        "fallen_leaves",
        "puddle",
        "rune",
        "torch",
        "bones",
        "rain_atmosphere",
        "snow_atmosphere",
        "fireflies_atmosphere",
    )

    def __init__(self) -> None:
        super().__init__()
        self.room.setdefault("layers", {}).setdefault("decorations", [])
        self.sync_decoration_presets()
        pygame.display.set_caption("BloomQuest Engine v0.13 — Map Pizzazz")
        self.status_message = "Decorations ready: animated accents, rain, snow, and fireflies."

    def sync_decoration_presets(self) -> None:
        with self.project_manager.engine_parts_file.open("r", encoding="utf-8") as handle:
            engine_payload = json.load(handle)
        project_path = self.project_manager.parts_file(self.project_id)
        with project_path.open("r", encoding="utf-8") as handle:
            project_payload = json.load(handle)

        existing = {part.get("id") for part in project_payload.get("parts", [])}
        changed = False
        for part in engine_payload.get("parts", []):
            if part.get("id") in self.DECORATION_IDS and part.get("id") not in existing:
                project_payload.setdefault("parts", []).append(deepcopy(part))
                existing.add(part.get("id"))
                changed = True

        if changed:
            with project_path.open("w", encoding="utf-8") as handle:
                json.dump(project_payload, handle, indent=2, ensure_ascii=False)
            self.load_project_parts()

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        super().open_project(project_id, save_current)
        self.room.setdefault("layers", {}).setdefault("decorations", [])
        if hasattr(self, "project_manager"):
            self.sync_decoration_presets()

    def switch_room(self, room_id: str) -> None:
        super().switch_room(room_id)
        self.room.setdefault("layers", {}).setdefault("decorations", [])

    def set_layer(self, layer: str) -> None:
        self.room.setdefault("layers", {}).setdefault(layer, [])
        self.active_layer = layer
        self.clear_selection()
        for index, part in enumerate(self.parts):
            if part.get("layer") == layer:
                self.selected_part_index = index
                break
        labels = {
            "map": "Map",
            "scene_objects": "Objects",
            "decorations": "Decorations",
            "actors": "Actors",
            "weapons": "Weapons",
            "weapons_effects": "Effects",
        }
        self.status_message = f"Layer: {labels.get(layer, layer)}"

    def place_or_select(self, gx: int, gy: int) -> None:
        before = len(self.room.get("layers", {}).get(self.active_layer, []))
        super().place_or_select(gx, gy)
        after = len(self.room.get("layers", {}).get(self.active_layer, []))

        if not self.selected_instance or after <= before:
            return

        preset = self.selected_part
        if preset.get("layer") == "decorations":
            for key in ("animation", "atmosphere", "hidden_in_play"):
                if key in preset:
                    self.selected_instance[key] = deepcopy(preset[key])
            self.status_message = f"Placed decoration: {preset.get('name', 'Decoration')}"

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            x, y = event.pos

            for rect, action in (
                (self.project_button, "projects"),
                (self.rooms_button, "rooms"),
                (self.help_button, "help"),
                (self.play_button, "play"),
            ):
                if rect.collidepoint(x, y):
                    if action == "play":
                        self.enter_play_mode()
                    else:
                        self.overlay = action
                        self.overlay_scroll = 0
                    return

            button_x = 205
            for layer in ("map", "scene_objects", "decorations", "actors", "weapons", "weapons_effects"):
                rect = pygame.Rect(button_x, 10, 92, 34)
                if rect.collidepoint(x, y):
                    self.set_layer(layer)
                    return
                button_x += 96
            return

        super().handle_click(event)

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, (35, 39, 47), (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.13", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

        if self.mode != "edit":
            return

        labels = {
            "map": "Map",
            "scene_objects": "Objects",
            "decorations": "Decor",
            "actors": "Actors",
            "weapons": "Weapons",
            "weapons_effects": "Effects",
        }
        button_x = 205
        for layer in labels:
            rect = pygame.Rect(button_x, 10, 92, 34)
            active = layer == self.active_layer
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(labels[layer], True, BACKGROUND if active else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))
            button_x += 96

        for rect, label in (
            (self.project_button, "Projects"),
            (self.rooms_button, "Rooms"),
            (self.help_button, "Help"),
            (self.play_button, "▶ Play"),
        ):
            active = label == "▶ Play"
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND if active else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))

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

        self.world_play = WorldPlayV13(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.13 — PLAY MODE")

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend([
                "## Map Pizzazz",
                "51. Open Decor and place flowers, grass, puddles, runes, torches, leaves, mushrooms, or bones.",
                "52. Decorations never block movement.",
                "53. Place one Rain, Snow, or Fireflies marker to affect the whole room.",
                "54. Atmosphere markers are visible in the editor but hidden during Play Mode.",
            ])
        else:
            content.extend([
                "## Decorations and Atmosphere",
                "Animated decorations add bobbing, swaying, pulsing, and flickering accents.",
                "Rain, snow, and fireflies create room-wide ambient particles.",
            ])
        return content
