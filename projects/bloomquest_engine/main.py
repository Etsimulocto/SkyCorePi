# main.py
# run with: python main.py
# path: projects/bloomquest_engine/main.py
# description: BloomQuest editor with premade parts, editable properties, JSON saving, and integrated play-test mode.
# version: 0.3.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, pygame, editor, playtest, grid, emoji, json
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: F5 or the Play button enters play mode. Esc returns to edit mode. Ctrl+S saves.
# uuid: bc-bloomquest-editor-0003

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pygame

from engine.play_mode import PlayMode


ROOT_DIR = Path(__file__).resolve().parent
PARTS_FILE = ROOT_DIR / "data" / "parts" / "parts_library.json"
ROOMS_DIR = ROOT_DIR / "data" / "rooms"
ROOM_FILE = ROOMS_DIR / "room_001.json"

WINDOW_WIDTH = 1360
WINDOW_HEIGHT = 840
FPS = 60
GRID_COLUMNS = 128
GRID_ROWS = 128
TILE_SIZE = 32
PALETTE_WIDTH = 250
PROPERTIES_WIDTH = 360
TOP_BAR_HEIGHT = 54
STATUS_BAR_HEIGHT = 30
CANVAS_LEFT = PALETTE_WIDTH
CANVAS_TOP = TOP_BAR_HEIGHT
CANVAS_RIGHT = WINDOW_WIDTH - PROPERTIES_WIDTH
CANVAS_BOTTOM = WINDOW_HEIGHT - STATUS_BAR_HEIGHT
CANVAS_WIDTH = CANVAS_RIGHT - CANVAS_LEFT
CANVAS_HEIGHT = CANVAS_BOTTOM - CANVAS_TOP

LAYER_ORDER = ["map", "scene_objects", "actors", "weapons_effects"]
LAYER_LABELS = {
    "map": "Map",
    "scene_objects": "Scene Objects",
    "actors": "Enemies / Player",
    "weapons_effects": "Weapons / Effects",
}
ACTION_TYPES = ["none", "show_text", "add_counter", "teleport", "damage_player", "heal_player", "timer"]

BACKGROUND = (25, 28, 34)
PANEL = (35, 39, 47)
PANEL_ALT = (43, 48, 58)
FIELD = (26, 30, 37)
TEXT = (235, 238, 244)
MUTED_TEXT = (165, 172, 184)
GRID_LINE = (65, 72, 84)
ACCENT = (110, 190, 130)
SELECTION = (245, 210, 90)
CANVAS_COLOR = (20, 23, 28)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def load_parts_library() -> list[dict[str, Any]]:
    payload = load_json(PARTS_FILE)
    parts = payload.get("parts", [])
    if not isinstance(parts, list):
        raise ValueError("parts_library.json must contain a parts list.")
    return parts


def blank_room() -> dict[str, Any]:
    return {
        "format": "bloomquest/room-v0.3",
        "room_id": "room_001",
        "name": "First Room",
        "grid": {"columns": GRID_COLUMNS, "rows": GRID_ROWS, "tile_size": TILE_SIZE},
        "layers": {layer_name: [] for layer_name in LAYER_ORDER},
        "counters": {"health": 3, "coins": 0, "score": 0, "keys": 0, "timer": 0},
    }


def load_room() -> dict[str, Any]:
    if not ROOM_FILE.exists():
        return blank_room()
    room = load_json(ROOM_FILE)
    room.setdefault("layers", {})
    for layer_name in LAYER_ORDER:
        room["layers"].setdefault(layer_name, [])
    room.setdefault("counters", {})
    return room


def save_room(room: dict[str, Any]) -> None:
    ROOMS_DIR.mkdir(parents=True, exist_ok=True)
    with ROOM_FILE.open("w", encoding="utf-8") as file_handle:
        json.dump(room, file_handle, indent=2, ensure_ascii=False)


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ("Segoe UI Emoji", "Segoe UI Symbol", "Arial Unicode MS", "DejaVu Sans", None):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)


def draw_text(surface: pygame.Surface, text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int] = TEXT) -> pygame.Rect:
    rendered = font.render(str(text), True, color)
    rect = rendered.get_rect(topleft=(x, y))
    surface.blit(rendered, rect)
    return rect


def safe_int(value: str, fallback: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return fallback


class TextField:
    def __init__(self, key: str, label: str, value: Any = "", multiline: bool = False, numeric: bool = False) -> None:
        self.key = key
        self.label = label
        self.value = str(value)
        self.multiline = multiline
        self.numeric = numeric
        self.active = False
        self.rect = pygame.Rect(0, 0, 0, 0)

    def handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.multiline:
                self.value += " "
            else:
                self.active = False
        elif event.key == pygame.K_TAB:
            self.active = False
        elif event.unicode and event.unicode.isprintable():
            if self.numeric and not (event.unicode.isdigit() or (event.unicode == "-" and not self.value)):
                return
            self.value += event.unicode


class BloomQuestEditor:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("BloomQuest Engine v0.3")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = get_font(16)
        self.font_medium = get_font(20)
        self.font_large = get_font(26, bold=True)
        self.font_emoji = get_font(23)

        self.parts = load_parts_library()
        self.room = load_room()
        self.active_layer = "map"
        self.selected_part_index = 0
        self.selected_instance: dict[str, Any] | None = None
        self.camera_x = 0
        self.camera_y = 0
        self.palette_scroll = 0
        self.properties_scroll = 0
        self.fields: list[TextField] = []
        self.field_by_key: dict[str, TextField] = {}
        self.apply_button = pygame.Rect(0, 0, 0, 0)
        self.action_button = pygame.Rect(0, 0, 0, 0)
        self.play_button = pygame.Rect(WINDOW_WIDTH - 110, 10, 92, 34)
        self.mode = "edit"
        self.play_mode: PlayMode | None = None
        self.status_message = "Ready. Place parts, edit properties, then press Play."
        self.running = True

    @property
    def selected_part(self) -> dict[str, Any]:
        return self.parts[self.selected_part_index]

    def visible_parts(self) -> list[tuple[int, dict[str, Any]]]:
        return [(index, part) for index, part in enumerate(self.parts) if part.get("layer") == self.active_layer]

    def run(self) -> None:
        while self.running:
            self.handle_events()
            if self.mode == "play" and self.play_mode:
                self.play_mode.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.mode == "play":
                    if self.play_mode and not self.play_mode.handle_key(event):
                        self.exit_play_mode()
                else:
                    self.handle_edit_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and self.mode == "edit":
                self.handle_edit_click(event)
            elif event.type == pygame.MOUSEWHEEL and self.mode == "edit":
                mouse_x, _ = pygame.mouse.get_pos()
                if mouse_x < PALETTE_WIDTH:
                    self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
                elif mouse_x >= CANVAS_RIGHT:
                    self.properties_scroll = max(0, self.properties_scroll - event.y * 34)
                else:
                    self.camera_y = max(0, self.camera_y - event.y * TILE_SIZE)

    def handle_edit_key(self, event: pygame.event.Event) -> None:
        active_field = next((field for field in self.fields if field.active), None)
        if active_field:
            active_field.handle_key(event)
            return

        control_down = bool(event.mod & pygame.KMOD_CTRL)
        if event.key == pygame.K_F5:
            self.enter_play_mode()
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif control_down and event.key == pygame.K_s:
            save_room(self.room)
            self.status_message = f"Saved {ROOM_FILE.name}"
        elif control_down and event.key == pygame.K_l:
            self.room = load_room()
            self.clear_selection()
            self.status_message = f"Loaded {ROOM_FILE.name}"
        elif event.key == pygame.K_DELETE and self.selected_instance:
            self.delete_selected()
        elif event.key == pygame.K_LEFT:
            self.camera_x = max(0, self.camera_x - TILE_SIZE)
        elif event.key == pygame.K_RIGHT:
            self.camera_x += TILE_SIZE
        elif event.key == pygame.K_UP:
            self.camera_y = max(0, self.camera_y - TILE_SIZE)
        elif event.key == pygame.K_DOWN:
            self.camera_y += TILE_SIZE
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.set_active_layer(LAYER_ORDER[event.key - pygame.K_1])

    def handle_edit_click(self, event: pygame.event.Event) -> None:
        x, y = event.pos
        if self.play_button.collidepoint(x, y):
            self.enter_play_mode()
            return

        for field in self.fields:
            field.active = field.rect.collidepoint(x, y)

        if self.apply_button.collidepoint(x, y):
            self.apply_property_changes()
            return
        if self.action_button.collidepoint(x, y):
            self.cycle_action_type()
            return
        if y < TOP_BAR_HEIGHT:
            self.handle_layer_click(x, y)
            return
        if x < PALETTE_WIDTH:
            self.handle_palette_click(x, y)
            return
        if x >= CANVAS_RIGHT:
            return
        if CANVAS_LEFT <= x < CANVAS_RIGHT and CANVAS_TOP <= y < CANVAS_BOTTOM:
            grid_x = (x - CANVAS_LEFT + self.camera_x) // TILE_SIZE
            grid_y = (y - CANVAS_TOP + self.camera_y) // TILE_SIZE
            if not (0 <= grid_x < GRID_COLUMNS and 0 <= grid_y < GRID_ROWS):
                return
            if event.button == 1:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.select_topmost(grid_x, grid_y)
                else:
                    self.place_or_select(grid_x, grid_y)
            elif event.button == 3:
                self.erase_at(grid_x, grid_y)

    def enter_play_mode(self) -> None:
        player_exists = any(instance.get("part_id") == "player" for instance in self.room["layers"].get("actors", []))
        if not player_exists:
            self.status_message = "Place a Player first."
            return

        colors = {"canvas": CANVAS_COLOR, "grid": GRID_LINE, "panel": PANEL, "text": TEXT, "accent": ACCENT}
        self.play_mode = PlayMode(
            self.room,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
            self.font_small,
            self.font_medium,
            self.font_emoji,
            colors,
        )
        self.mode = "play"
        self.status_message = self.play_mode.status
        pygame.display.set_caption("BloomQuest Engine v0.3 — PLAY MODE")

    def exit_play_mode(self) -> None:
        self.mode = "edit"
        self.play_mode = None
        self.status_message = "Returned to Edit Mode. Play-test changes were discarded."
        pygame.display.set_caption("BloomQuest Engine v0.3")

    def handle_layer_click(self, x: int, y: int) -> None:
        button_x = 300
        for layer_name in LAYER_ORDER:
            rect = pygame.Rect(button_x, 10, 145, 34)
            if rect.collidepoint(x, y):
                self.set_active_layer(layer_name)
                return
            button_x += 153

    def set_active_layer(self, layer_name: str) -> None:
        self.active_layer = layer_name
        self.clear_selection()
        self.palette_scroll = 0
        for index, part in enumerate(self.parts):
            if part.get("layer") == layer_name:
                self.selected_part_index = index
                break
        self.status_message = f"Layer: {LAYER_LABELS[layer_name]}"

    def handle_palette_click(self, x: int, y: int) -> None:
        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        for row, (index, part) in enumerate(self.visible_parts()):
            rect = pygame.Rect(10, start_y + row * 48, PALETTE_WIDTH - 20, 42)
            if rect.collidepoint(x, y):
                self.selected_part_index = index
                self.clear_selection()
                self.status_message = f"Selected {part['name']}"
                return

    def find_instance_at(self, grid_x: int, grid_y: int, layer_name: str | None = None) -> dict[str, Any] | None:
        layers = [layer_name] if layer_name else list(reversed(LAYER_ORDER))
        for current_layer in layers:
            for instance in reversed(self.room["layers"].get(current_layer, [])):
                if instance.get("x") == grid_x and instance.get("y") == grid_y:
                    return instance
        return None

    def select_topmost(self, grid_x: int, grid_y: int) -> None:
        instance = self.find_instance_at(grid_x, grid_y)
        if instance:
            self.selected_instance = instance
            self.active_layer = instance.get("layer", self.active_layer)
            self.build_fields()
            self.status_message = f"Selected {instance.get('name', 'part')}"
        else:
            self.clear_selection()

    def place_or_select(self, grid_x: int, grid_y: int) -> None:
        existing = self.find_instance_at(grid_x, grid_y, self.active_layer)
        selected = self.selected_part
        if existing and existing.get("part_id") == selected.get("id"):
            self.selected_instance = existing
            self.build_fields()
            return
        if existing:
            self.room["layers"][self.active_layer].remove(existing)

        number = len(self.room["layers"][self.active_layer]) + 1
        instance = {
            "instance_id": f"{selected['id']}_{number:04d}",
            "part_id": selected["id"],
            "emoji": selected.get("emoji", ""),
            "name": selected.get("name", selected["id"]),
            "description": selected.get("description", ""),
            "layer": selected.get("layer", self.active_layer),
            "x": grid_x,
            "y": grid_y,
            "color": selected.get("color", [180, 180, 180]),
            "solid": selected.get("solid", False),
            "enabled": True,
        }
        for key in ("action", "health", "damage"):
            if key in selected:
                instance[key] = deepcopy(selected[key])
        self.room["layers"][self.active_layer].append(instance)
        self.selected_instance = instance
        self.build_fields()
        self.status_message = f"Placed {instance['name']} at {grid_x}, {grid_y}"

    def erase_at(self, grid_x: int, grid_y: int) -> None:
        instance = self.find_instance_at(grid_x, grid_y, self.active_layer)
        if instance:
            self.room["layers"][self.active_layer].remove(instance)
            if instance is self.selected_instance:
                self.clear_selection()
            self.status_message = f"Erased part at {grid_x}, {grid_y}"

    def delete_selected(self) -> None:
        if not self.selected_instance:
            return
        layer = self.room["layers"].get(self.selected_instance.get("layer", self.active_layer), [])
        if self.selected_instance in layer:
            layer.remove(self.selected_instance)
        self.clear_selection()

    def clear_selection(self) -> None:
        self.selected_instance = None
        self.fields = []
        self.field_by_key = {}
        self.properties_scroll = 0

    def build_fields(self) -> None:
        if not self.selected_instance:
            return
        target = self.selected_instance
        action = target.get("action", {})
        self.fields = [
            TextField("name", "Name", target.get("name", "")),
            TextField("description", "Description", target.get("description", ""), multiline=True),
            TextField("text", "Text / Dialogue", action.get("text", ""), multiline=True),
            TextField("counter", "Counter", action.get("counter", "")),
            TextField("amount", "Value / Amount", action.get("amount", 0), numeric=True),
            TextField("health", "Health", target.get("health", 0), numeric=True),
            TextField("damage", "Damage", target.get("damage", 0), numeric=True),
            TextField("target_room", "Target Room", action.get("target_room", "")),
            TextField("target_x", "Target X", action.get("target_x", 0), numeric=True),
            TextField("target_y", "Target Y", action.get("target_y", 0), numeric=True),
            TextField("seconds", "Timer Seconds", action.get("seconds", 0), numeric=True),
        ]
        self.field_by_key = {field.key: field for field in self.fields}
        self.properties_scroll = 0

    def cycle_action_type(self) -> None:
        if not self.selected_instance:
            return
        action = self.selected_instance.setdefault("action", {})
        current = action.get("type", "none")
        try:
            index = ACTION_TYPES.index(current)
        except ValueError:
            index = 0
        action["type"] = ACTION_TYPES[(index + 1) % len(ACTION_TYPES)]
        self.status_message = f"Action type: {action['type']}"

    def apply_property_changes(self) -> None:
        if not self.selected_instance:
            return
        target = self.selected_instance
        target["name"] = self.field_by_key["name"].value.strip() or "Part"
        target["description"] = self.field_by_key["description"].value.strip()
        target["health"] = safe_int(self.field_by_key["health"].value, target.get("health", 0))
        target["damage"] = safe_int(self.field_by_key["damage"].value, target.get("damage", 0))
        action = target.setdefault("action", {})
        action["text"] = self.field_by_key["text"].value.strip()
        action["counter"] = self.field_by_key["counter"].value.strip()
        action["amount"] = safe_int(self.field_by_key["amount"].value, action.get("amount", 0))
        action["target_room"] = self.field_by_key["target_room"].value.strip()
        action["target_x"] = safe_int(self.field_by_key["target_x"].value, action.get("target_x", 0))
        action["target_y"] = safe_int(self.field_by_key["target_y"].value, action.get("target_y", 0))
        action["seconds"] = safe_int(self.field_by_key["seconds"].value, action.get("seconds", 0))
        self.status_message = f"Updated {target['name']}"

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.draw_top_bar()
        if self.mode == "play" and self.play_mode:
            self.draw_play_mode()
        else:
            self.draw_palette()
            self.draw_canvas(self.camera_x, self.camera_y, True)
            self.draw_properties()
        self.draw_status()

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
        title = "BloomQuest v0.3 — PLAY" if self.mode == "play" else "BloomQuest v0.3"
        draw_text(self.screen, title, 16, 13, self.font_large)

        if self.mode == "edit":
            x = 300
            for layer_name in LAYER_ORDER:
                active = layer_name == self.active_layer
                rect = pygame.Rect(x, 10, 145, 34)
                pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
                label = self.font_small.render(LAYER_LABELS[layer_name], True, BACKGROUND if active else TEXT)
                self.screen.blit(label, label.get_rect(center=rect.center))
                x += 153

            pygame.draw.rect(self.screen, ACCENT, self.play_button, border_radius=6)
            play_label = self.font_small.render("▶ Play", True, BACKGROUND)
            self.screen.blit(play_label, play_label.get_rect(center=self.play_button.center))

    def draw_palette(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Premade Parts", 14, TOP_BAR_HEIGHT + 12, self.font_medium)
        draw_text(self.screen, LAYER_LABELS[self.active_layer], 14, TOP_BAR_HEIGHT + 36, self.font_small, MUTED_TEXT)
        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        for row, (index, part) in enumerate(self.visible_parts()):
            y = start_y + row * 48
            if y + 42 < TOP_BAR_HEIGHT + 58 or y > CANVAS_BOTTOM:
                continue
            rect = pygame.Rect(10, y, PALETTE_WIDTH - 20, 42)
            pygame.draw.rect(self.screen, (72, 83, 78) if index == self.selected_part_index else PANEL_ALT, rect, border_radius=5)
            icon_rect = pygame.Rect(16, y + 6, 30, 30)
            pygame.draw.rect(self.screen, tuple(part.get("color", [180, 180, 180])), icon_rect, border_radius=4)
            emoji = part.get("emoji", "")
            if emoji:
                image = self.font_emoji.render(emoji, True, TEXT)
                self.screen.blit(image, image.get_rect(center=icon_rect.center))
            draw_text(self.screen, part.get("name", "Part"), 54, y + 11, self.font_small)

    def draw_canvas(self, camera_x: int, camera_y: int, show_selection: bool) -> None:
        rect = pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, CANVAS_COLOR, rect)
        self.screen.set_clip(rect)
        start_col = camera_x // TILE_SIZE
        start_row = camera_y // TILE_SIZE
        end_col = start_col + CANVAS_WIDTH // TILE_SIZE + 2
        end_row = start_row + CANVAS_HEIGHT // TILE_SIZE + 2
        for grid_y in range(start_row, end_row):
            for grid_x in range(start_col, end_col):
                sx = CANVAS_LEFT + grid_x * TILE_SIZE - camera_x
                sy = CANVAS_TOP + grid_y * TILE_SIZE - camera_y
                pygame.draw.rect(self.screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), width=1)
        for layer_name in LAYER_ORDER:
            for instance in self.room["layers"].get(layer_name, []):
                self.draw_instance(self.screen, instance, camera_x, camera_y, show_selection)
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, rect, width=1)

    def draw_instance(self, surface: pygame.Surface, instance: dict[str, Any], camera_x: int, camera_y: int, show_selection: bool) -> None:
        sx = CANVAS_LEFT + int(instance.get("x", 0)) * TILE_SIZE - camera_x
        sy = CANVAS_TOP + int(instance.get("y", 0)) * TILE_SIZE - camera_y
        if sx + TILE_SIZE < CANVAS_LEFT or sx > CANVAS_RIGHT or sy + TILE_SIZE < CANVAS_TOP or sy > CANVAS_BOTTOM:
            return
        rect = pygame.Rect(sx + 1, sy + 1, TILE_SIZE - 2, TILE_SIZE - 2)
        pygame.draw.rect(surface, tuple(instance.get("color", [180, 180, 180])), rect, border_radius=3)
        emoji = instance.get("emoji", "")
        if emoji:
            image = self.font_emoji.render(emoji, True, TEXT)
            surface.blit(image, image.get_rect(center=rect.center))
        if show_selection and instance is self.selected_instance:
            pygame.draw.rect(surface, SELECTION, rect, width=3, border_radius=3)

    def draw_properties(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Properties", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 14, self.font_medium)
        if not self.selected_instance:
            draw_text(self.screen, "Place a part, then click it again", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 68, self.font_small, MUTED_TEXT)
            draw_text(self.screen, "to edit its fields.", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 92, self.font_small, MUTED_TEXT)
            return

        target = self.selected_instance
        y = TOP_BAR_HEIGHT + 52 - self.properties_scroll
        emoji = target.get("emoji", "")
        if emoji:
            draw_text(self.screen, emoji, CANVAS_RIGHT + 16, y, self.font_large)
            draw_text(self.screen, target.get("name", "Part"), CANVAS_RIGHT + 54, y + 2, self.font_medium)
        else:
            draw_text(self.screen, target.get("name", "Part"), CANVAS_RIGHT + 16, y + 2, self.font_medium)
        y += 48
        draw_text(self.screen, "Action Type", CANVAS_RIGHT + 16, y, self.font_small, MUTED_TEXT)
        y += 22
        self.action_button = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, 34)
        pygame.draw.rect(self.screen, PANEL_ALT, self.action_button, border_radius=5)
        action_name = target.get("action", {}).get("type", "none")
        label = self.font_small.render(action_name, True, TEXT)
        self.screen.blit(label, label.get_rect(center=self.action_button.center))
        y += 48

        for field in self.fields:
            draw_text(self.screen, field.label, CANVAS_RIGHT + 16, y, self.font_small, MUTED_TEXT)
            y += 21
            height = 54 if field.multiline else 34
            field.rect = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, height)
            pygame.draw.rect(self.screen, (52, 61, 72) if field.active else FIELD, field.rect, border_radius=5)
            pygame.draw.rect(self.screen, ACCENT if field.active else GRID_LINE, field.rect, width=2, border_radius=5)
            value = field.value[-78 if field.multiline else -34:]
            draw_text(self.screen, value, field.rect.x + 7, field.rect.y + 7, self.font_small)
            y += height + 11

        self.apply_button = pygame.Rect(CANVAS_RIGHT + 16, y + 4, PROPERTIES_WIDTH - 32, 40)
        pygame.draw.rect(self.screen, ACCENT, self.apply_button, border_radius=6)
        label = self.font_small.render("Apply Changes", True, BACKGROUND)
        self.screen.blit(label, label.get_rect(center=self.apply_button.center))

    def draw_play_mode(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "PLAY MODE", 18, TOP_BAR_HEIGHT + 18, self.font_medium)
        draw_text(self.screen, "WASD / Arrows", 18, TOP_BAR_HEIGHT + 62, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "E = interact", 18, TOP_BAR_HEIGHT + 86, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Esc = return", 18, TOP_BAR_HEIGHT + 110, self.font_small, MUTED_TEXT)

        pygame.draw.rect(self.screen, PANEL, (CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Live Counters", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 18, self.font_medium)
        if self.play_mode:
            y = TOP_BAR_HEIGHT + 62
            for key, value in self.play_mode.counters.items():
                draw_text(self.screen, f"{key}: {value}", CANVAS_RIGHT + 16, y, self.font_small)
                y += 26
            self.status_message = self.play_mode.status
            self.play_mode.draw(self.screen, self.draw_instance)

    def draw_status(self) -> None:
        pygame.draw.rect(self.screen, PANEL_ALT, (0, WINDOW_HEIGHT - STATUS_BAR_HEIGHT, WINDOW_WIDTH, STATUS_BAR_HEIGHT))
        draw_text(self.screen, self.status_message, 12, WINDOW_HEIGHT - 23, self.font_small)
        right = "F5 Play | Ctrl+S Save" if self.mode == "edit" else "Esc Return to Edit"
        image = self.font_small.render(right, True, MUTED_TEXT)
        self.screen.blit(image, image.get_rect(midright=(WINDOW_WIDTH - 12, WINDOW_HEIGHT - 15)))


def main() -> int:
    try:
        BloomQuestEditor().run()
        return 0
    except Exception as error:
        print("BloomQuest failed to start.")
        print(f"Reason: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
