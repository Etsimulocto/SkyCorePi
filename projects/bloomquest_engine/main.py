# main.py
# run with: python main.py
# path: projects/bloomquest_engine/main.py
# description: BloomQuest editor with a 128x128 grid, premade parts, four layers, editable properties, and JSON room saving.
# version: 0.2.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, pygame, editor, grid, emoji, json, properties
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Left-click places/selects. Right-click erases. Shift+left-click selects the topmost object. Ctrl+S saves. Ctrl+L loads.
# uuid: bc-bloomquest-editor-0002

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pygame


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

ACTION_TYPES = [
    "none",
    "show_text",
    "add_counter",
    "teleport",
    "damage_player",
    "heal_player",
    "timer",
]

BACKGROUND = (25, 28, 34)
PANEL = (35, 39, 47)
PANEL_ALT = (43, 48, 58)
FIELD = (26, 30, 37)
TEXT = (235, 238, 244)
MUTED_TEXT = (165, 172, 184)
GRID_LINE = (65, 72, 84)
ACCENT = (110, 190, 130)
SELECTION = (245, 210, 90)
DANGER = (215, 85, 85)


def load_parts_library() -> list[dict[str, Any]]:
    if not PARTS_FILE.exists():
        raise FileNotFoundError(f"Missing parts library: {PARTS_FILE}")

    with PARTS_FILE.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    parts = payload.get("parts", [])
    if not isinstance(parts, list):
        raise ValueError("parts_library.json must contain a 'parts' list.")

    return parts


def make_blank_room() -> dict[str, Any]:
    return {
        "format": "bloomquest/room-v0.2",
        "room_id": "room_001",
        "name": "First Room",
        "grid": {
            "columns": GRID_COLUMNS,
            "rows": GRID_ROWS,
            "tile_size": TILE_SIZE,
        },
        "layers": {layer_name: [] for layer_name in LAYER_ORDER},
        "counters": {
            "health": 3,
            "coins": 0,
            "score": 0,
            "keys": 0,
            "timer": 0,
        },
    }


def save_room(room: dict[str, Any]) -> None:
    ROOMS_DIR.mkdir(parents=True, exist_ok=True)
    with ROOM_FILE.open("w", encoding="utf-8") as file_handle:
        json.dump(room, file_handle, indent=2, ensure_ascii=False)


def load_room() -> dict[str, Any]:
    if not ROOM_FILE.exists():
        return make_blank_room()

    with ROOM_FILE.open("r", encoding="utf-8") as file_handle:
        room = json.load(file_handle)

    room.setdefault("layers", {})
    for layer_name in LAYER_ORDER:
        room["layers"].setdefault(layer_name, [])

    return room


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    preferred_fonts = [
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Arial Unicode MS",
        "DejaVu Sans",
        None,
    ]

    for font_name in preferred_fonts:
        try:
            return pygame.font.SysFont(font_name, size, bold=bold)
        except Exception:
            continue

    return pygame.font.Font(None, size)


def draw_text(
    surface: pygame.Surface,
    text: str,
    position: tuple[int, int],
    font: pygame.font.Font,
    color: tuple[int, int, int] = TEXT,
) -> pygame.Rect:
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(topleft=position)
    surface.blit(rendered, rect)
    return rect


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def safe_int(value: str, fallback: int = 0) -> int:
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return fallback


class TextField:
    def __init__(
        self,
        key: str,
        label: str,
        value: str = "",
        multiline: bool = False,
        numeric: bool = False,
    ) -> None:
        self.key = key
        self.label = label
        self.value = str(value)
        self.multiline = multiline
        self.numeric = numeric
        self.active = False
        self.rect = pygame.Rect(0, 0, 100, 32)

    def handle_key(self, event: pygame.event.Event) -> None:
        if not self.active:
            return

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
        pygame.display.set_caption("BloomQuest Engine v0.2")

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

        self.status_message = "Ready. Choose a part and click the grid."
        self.running = True

    @property
    def selected_part(self) -> dict[str, Any]:
        return self.parts[self.selected_part_index]

    def visible_parts(self) -> list[tuple[int, dict[str, Any]]]:
        return [
            (index, part)
            for index, part in enumerate(self.parts)
            if part.get("layer") == self.active_layer
        ]

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event)

            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, _ = pygame.mouse.get_pos()
                if mouse_x < PALETTE_WIDTH:
                    self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
                elif mouse_x >= CANVAS_RIGHT:
                    self.properties_scroll = max(0, self.properties_scroll - event.y * 34)
                elif CANVAS_LEFT <= mouse_x < CANVAS_RIGHT:
                    self.camera_y = clamp(
                        self.camera_y - event.y * TILE_SIZE,
                        0,
                        max(0, GRID_ROWS * TILE_SIZE - CANVAS_HEIGHT),
                    )

    def handle_keydown(self, event: pygame.event.Event) -> None:
        active_field = next((field for field in self.fields if field.active), None)
        if active_field is not None:
            active_field.handle_key(event)
            return

        control_down = bool(event.mod & pygame.KMOD_CTRL)

        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif control_down and event.key == pygame.K_s:
            save_room(self.room)
            self.status_message = f"Saved {ROOM_FILE.name}"
        elif control_down and event.key == pygame.K_l:
            self.room = load_room()
            self.clear_selection()
            self.status_message = f"Loaded {ROOM_FILE.name}"
        elif event.key == pygame.K_DELETE and self.selected_instance is not None:
            self.delete_selected_instance()
        elif event.key == pygame.K_LEFT:
            self.camera_x = max(0, self.camera_x - TILE_SIZE)
        elif event.key == pygame.K_RIGHT:
            self.camera_x = min(max(0, GRID_COLUMNS * TILE_SIZE - CANVAS_WIDTH), self.camera_x + TILE_SIZE)
        elif event.key == pygame.K_UP:
            self.camera_y = max(0, self.camera_y - TILE_SIZE)
        elif event.key == pygame.K_DOWN:
            self.camera_y = min(max(0, GRID_ROWS * TILE_SIZE - CANVAS_HEIGHT), self.camera_y + TILE_SIZE)
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.set_active_layer(LAYER_ORDER[event.key - pygame.K_1])

    def handle_mouse_down(self, event: pygame.event.Event) -> None:
        mouse_x, mouse_y = event.pos

        for field in self.fields:
            field.active = field.rect.collidepoint(mouse_x, mouse_y)

        if self.apply_button.collidepoint(mouse_x, mouse_y):
            self.apply_property_changes()
            return

        if self.action_button.collidepoint(mouse_x, mouse_y):
            self.cycle_action_type()
            return

        if mouse_y < TOP_BAR_HEIGHT:
            self.handle_top_bar_click(mouse_x, mouse_y)
            return

        if mouse_x < PALETTE_WIDTH:
            self.handle_palette_click(mouse_x, mouse_y)
            return

        if mouse_x >= CANVAS_RIGHT:
            return

        if CANVAS_LEFT <= mouse_x < CANVAS_RIGHT and CANVAS_TOP <= mouse_y < CANVAS_BOTTOM:
            grid_x, grid_y = self.screen_to_grid(mouse_x, mouse_y)
            if not self.grid_position_valid(grid_x, grid_y):
                return

            if event.button == 1:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.select_topmost(grid_x, grid_y)
                else:
                    self.place_or_select_part(grid_x, grid_y)
            elif event.button == 3:
                self.erase_at(grid_x, grid_y)

    def handle_top_bar_click(self, mouse_x: int, mouse_y: int) -> None:
        button_x = 310
        button_width = 155

        for layer_name in LAYER_ORDER:
            button_rect = pygame.Rect(button_x, 10, button_width, 34)
            if button_rect.collidepoint(mouse_x, mouse_y):
                self.set_active_layer(layer_name)
                return
            button_x += button_width + 8

    def set_active_layer(self, layer_name: str) -> None:
        self.active_layer = layer_name
        self.clear_selection()
        self.palette_scroll = 0

        for index, part in enumerate(self.parts):
            if part.get("layer") == layer_name:
                self.selected_part_index = index
                break

        self.status_message = f"Layer: {LAYER_LABELS[layer_name]}"

    def handle_palette_click(self, mouse_x: int, mouse_y: int) -> None:
        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        row_height = 48

        for visible_row, (part_index, part) in enumerate(self.visible_parts()):
            row_rect = pygame.Rect(10, start_y + visible_row * row_height, PALETTE_WIDTH - 20, 42)
            if row_rect.collidepoint(mouse_x, mouse_y):
                self.selected_part_index = part_index
                self.clear_selection()
                self.status_message = f"Selected {part['name']}"
                return

    def screen_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int]:
        world_x = mouse_x - CANVAS_LEFT + self.camera_x
        world_y = mouse_y - CANVAS_TOP + self.camera_y
        return world_x // TILE_SIZE, world_y // TILE_SIZE

    def grid_position_valid(self, grid_x: int, grid_y: int) -> bool:
        return 0 <= grid_x < GRID_COLUMNS and 0 <= grid_y < GRID_ROWS

    def find_instance_at(self, grid_x: int, grid_y: int, layer_name: str | None = None) -> dict[str, Any] | None:
        layers = [layer_name] if layer_name else list(reversed(LAYER_ORDER))
        for current_layer in layers:
            for instance in reversed(self.room["layers"].get(current_layer, [])):
                if instance.get("x") == grid_x and instance.get("y") == grid_y:
                    return instance
        return None

    def select_topmost(self, grid_x: int, grid_y: int) -> None:
        instance = self.find_instance_at(grid_x, grid_y)
        if instance is None:
            self.clear_selection()
            self.status_message = "Nothing selected."
            return

        self.selected_instance = instance
        self.active_layer = instance.get("layer", self.active_layer)
        self.build_property_fields()
        self.status_message = f"Selected {instance.get('name', 'part')}"

    def place_or_select_part(self, grid_x: int, grid_y: int) -> None:
        existing = self.find_instance_at(grid_x, grid_y, self.active_layer)
        selected_part = self.selected_part

        if existing and existing.get("part_id") == selected_part.get("id"):
            self.selected_instance = existing
            self.build_property_fields()
            self.status_message = f"Selected placed {existing.get('name', 'part')}"
            return

        if existing:
            self.room["layers"][self.active_layer].remove(existing)

        instance_number = len(self.room["layers"][self.active_layer]) + 1
        instance = {
            "instance_id": f"{selected_part['id']}_{instance_number:04d}",
            "part_id": selected_part["id"],
            "emoji": selected_part.get("emoji", ""),
            "name": selected_part.get("name", selected_part["id"]),
            "description": selected_part.get("description", ""),
            "layer": selected_part.get("layer", self.active_layer),
            "x": grid_x,
            "y": grid_y,
            "color": selected_part.get("color", [180, 180, 180]),
            "solid": selected_part.get("solid", False),
            "enabled": True,
        }

        for optional_key in ("action", "health", "damage"):
            if optional_key in selected_part:
                instance[optional_key] = deepcopy(selected_part[optional_key])

        self.room["layers"][self.active_layer].append(instance)
        self.selected_instance = instance
        self.build_property_fields()
        self.status_message = f"Placed {instance['name']} at {grid_x}, {grid_y}"

    def erase_at(self, grid_x: int, grid_y: int) -> None:
        existing = self.find_instance_at(grid_x, grid_y, self.active_layer)
        if existing is None:
            return

        self.room["layers"][self.active_layer].remove(existing)
        if self.selected_instance is existing:
            self.clear_selection()
        self.status_message = f"Erased part at {grid_x}, {grid_y}"

    def delete_selected_instance(self) -> None:
        if self.selected_instance is None:
            return

        layer_name = self.selected_instance.get("layer", self.active_layer)
        layer_items = self.room["layers"].get(layer_name, [])
        if self.selected_instance in layer_items:
            name = self.selected_instance.get("name", "part")
            layer_items.remove(self.selected_instance)
            self.status_message = f"Deleted {name}"
        self.clear_selection()

    def clear_selection(self) -> None:
        self.selected_instance = None
        self.fields = []
        self.field_by_key = {}
        self.properties_scroll = 0

    def build_property_fields(self) -> None:
        if self.selected_instance is None:
            self.fields = []
            self.field_by_key = {}
            return

        target = self.selected_instance
        action = target.get("action", {})

        fields = [
            TextField("name", "Name", target.get("name", "")),
            TextField("description", "Description", target.get("description", ""), multiline=True),
            TextField("text", "Text / Dialogue", action.get("text", ""), multiline=True),
            TextField("counter", "Counter", action.get("counter", "")),
            TextField("amount", "Value / Amount", action.get("amount", "0"), numeric=True),
            TextField("health", "Health", target.get("health", "0"), numeric=True),
            TextField("damage", "Damage", target.get("damage", "0"), numeric=True),
            TextField("target_room", "Target Room", action.get("target_room", "")),
            TextField("target_x", "Target X", action.get("target_x", "0"), numeric=True),
            TextField("target_y", "Target Y", action.get("target_y", "0"), numeric=True),
            TextField("seconds", "Timer Seconds", action.get("seconds", "0"), numeric=True),
        ]

        self.fields = fields
        self.field_by_key = {field.key: field for field in fields}
        self.properties_scroll = 0

    def cycle_action_type(self) -> None:
        if self.selected_instance is None:
            return

        action = self.selected_instance.setdefault("action", {})
        current_type = action.get("type", "none")
        try:
            current_index = ACTION_TYPES.index(current_type)
        except ValueError:
            current_index = 0

        action["type"] = ACTION_TYPES[(current_index + 1) % len(ACTION_TYPES)]
        self.status_message = f"Action type: {action['type']}"

    def apply_property_changes(self) -> None:
        if self.selected_instance is None:
            return

        target = self.selected_instance
        target["name"] = self.field_by_key["name"].value.strip() or target.get("name", "Part")
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
        self.draw_palette()
        self.draw_canvas()
        self.draw_properties_panel()
        self.draw_status_bar()

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.2", (16, 13), self.font_large)

        button_x = 310
        button_width = 155
        for layer_name in LAYER_ORDER:
            is_active = layer_name == self.active_layer
            button_color = ACCENT if is_active else PANEL_ALT
            text_color = BACKGROUND if is_active else TEXT
            button_rect = pygame.Rect(button_x, 10, button_width, 34)
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=6)
            label_surface = self.font_small.render(LAYER_LABELS[layer_name], True, text_color)
            self.screen.blit(label_surface, label_surface.get_rect(center=button_rect.center))
            button_x += button_width + 8

    def draw_palette(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Premade Parts", (14, TOP_BAR_HEIGHT + 12), self.font_medium)
        draw_text(self.screen, LAYER_LABELS[self.active_layer], (14, TOP_BAR_HEIGHT + 36), self.font_small, MUTED_TEXT)

        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        row_height = 48

        for visible_row, (part_index, part) in enumerate(self.visible_parts()):
            row_y = start_y + visible_row * row_height
            if row_y + 42 < TOP_BAR_HEIGHT + 58 or row_y > CANVAS_BOTTOM:
                continue

            row_color = (72, 83, 78) if part_index == self.selected_part_index else PANEL_ALT
            row_rect = pygame.Rect(10, row_y, PALETTE_WIDTH - 20, 42)
            pygame.draw.rect(self.screen, row_color, row_rect, border_radius=5)

            icon_rect = pygame.Rect(16, row_y + 6, 30, 30)
            pygame.draw.rect(self.screen, tuple(part.get("color", [180, 180, 180])), icon_rect, border_radius=4)

            emoji = part.get("emoji", "")
            if emoji:
                emoji_surface = self.font_emoji.render(emoji, True, TEXT)
                self.screen.blit(emoji_surface, emoji_surface.get_rect(center=icon_rect.center))

            draw_text(self.screen, part.get("name", "Part"), (54, row_y + 11), self.font_small)

        pygame.draw.line(self.screen, GRID_LINE, (PALETTE_WIDTH - 1, TOP_BAR_HEIGHT), (PALETTE_WIDTH - 1, WINDOW_HEIGHT))

    def draw_canvas(self) -> None:
        canvas_rect = pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, (20, 23, 28), canvas_rect)
        self.screen.set_clip(canvas_rect)

        start_column = self.camera_x // TILE_SIZE
        start_row = self.camera_y // TILE_SIZE
        end_column = min(GRID_COLUMNS, start_column + CANVAS_WIDTH // TILE_SIZE + 2)
        end_row = min(GRID_ROWS, start_row + CANVAS_HEIGHT // TILE_SIZE + 2)

        for grid_y in range(start_row, end_row):
            for grid_x in range(start_column, end_column):
                screen_x = CANVAS_LEFT + grid_x * TILE_SIZE - self.camera_x
                screen_y = CANVAS_TOP + grid_y * TILE_SIZE - self.camera_y
                pygame.draw.rect(self.screen, GRID_LINE, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), width=1)

        for layer_name in LAYER_ORDER:
            for instance in self.room["layers"].get(layer_name, []):
                self.draw_instance(instance)

        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, canvas_rect, width=1)

    def draw_instance(self, instance: dict[str, Any]) -> None:
        screen_x = CANVAS_LEFT + int(instance.get("x", 0)) * TILE_SIZE - self.camera_x
        screen_y = CANVAS_TOP + int(instance.get("y", 0)) * TILE_SIZE - self.camera_y

        if screen_x + TILE_SIZE < CANVAS_LEFT or screen_x > CANVAS_RIGHT:
            return
        if screen_y + TILE_SIZE < CANVAS_TOP or screen_y > CANVAS_BOTTOM:
            return

        cell_rect = pygame.Rect(screen_x + 1, screen_y + 1, TILE_SIZE - 2, TILE_SIZE - 2)
        pygame.draw.rect(self.screen, tuple(instance.get("color", [180, 180, 180])), cell_rect, border_radius=3)

        emoji = instance.get("emoji", "")
        if emoji:
            emoji_surface = self.font_emoji.render(emoji, True, TEXT)
            self.screen.blit(emoji_surface, emoji_surface.get_rect(center=cell_rect.center))

        if instance is self.selected_instance:
            pygame.draw.rect(self.screen, SELECTION, cell_rect, width=3, border_radius=3)

    def draw_properties_panel(self) -> None:
        panel_rect = pygame.Rect(CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL, panel_rect)
        pygame.draw.line(self.screen, GRID_LINE, (CANVAS_RIGHT, TOP_BAR_HEIGHT), (CANVAS_RIGHT, WINDOW_HEIGHT))

        draw_text(self.screen, "Properties", (CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 14), self.font_medium)

        if self.selected_instance is None:
            target = self.selected_part
            y = TOP_BAR_HEIGHT + 62
            emoji = target.get("emoji", "")
            if emoji:
                draw_text(self.screen, emoji, (CANVAS_RIGHT + 16, y), self.font_large)
                draw_text(self.screen, target.get("name", "Part"), (CANVAS_RIGHT + 54, y + 2), self.font_medium)
            else:
                draw_text(self.screen, target.get("name", "Part"), (CANVAS_RIGHT + 16, y + 2), self.font_medium)

            y += 52
            draw_text(self.screen, "Place a part, then click it again", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            y += 22
            draw_text(self.screen, "to edit its name, text, action,", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            y += 22
            draw_text(self.screen, "health, damage, target, and timer.", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            return

        target = self.selected_instance
        y = TOP_BAR_HEIGHT + 52 - self.properties_scroll

        emoji = target.get("emoji", "")
        if emoji:
            draw_text(self.screen, emoji, (CANVAS_RIGHT + 16, y), self.font_large)
            draw_text(self.screen, target.get("name", "Part"), (CANVAS_RIGHT + 54, y + 2), self.font_medium)
        else:
            draw_text(self.screen, target.get("name", "Part"), (CANVAS_RIGHT + 16, y + 2), self.font_medium)

        y += 44
        draw_text(self.screen, f"Layer: {LAYER_LABELS.get(target.get('layer', ''), 'Unknown')}", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
        y += 24
        draw_text(self.screen, f"Grid: {target.get('x', 0)}, {target.get('y', 0)}", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
        y += 34

        action = target.get("action", {})
        draw_text(self.screen, "Action Type", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
        y += 22
        self.action_button = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, 34)
        pygame.draw.rect(self.screen, PANEL_ALT, self.action_button, border_radius=5)
        action_name = action.get("type", "none")
        action_surface = self.font_small.render(action_name, True, TEXT)
        self.screen.blit(action_surface, action_surface.get_rect(center=self.action_button.center))
        y += 48

        for field in self.fields:
            draw_text(self.screen, field.label, (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            y += 21

            field_height = 54 if field.multiline else 34
            field.rect = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, field_height)
            field_color = (52, 61, 72) if field.active else FIELD
            pygame.draw.rect(self.screen, field_color, field.rect, border_radius=5)
            pygame.draw.rect(self.screen, ACCENT if field.active else GRID_LINE, field.rect, width=2, border_radius=5)

            display_value = field.value
            max_chars = 78 if field.multiline else 34
            if len(display_value) > max_chars:
                display_value = display_value[-max_chars:]

            lines = self.wrap_text(display_value, field.rect.width - 12, self.font_small)
            for line_index, line in enumerate(lines[:2 if field.multiline else 1]):
                draw_text(self.screen, line, (field.rect.x + 7, field.rect.y + 7 + line_index * 19), self.font_small)

            y += field_height + 11

        self.apply_button = pygame.Rect(CANVAS_RIGHT + 16, y + 4, PROPERTIES_WIDTH - 32, 40)
        pygame.draw.rect(self.screen, ACCENT, self.apply_button, border_radius=6)
        apply_surface = self.font_small.render("Apply Changes", True, BACKGROUND)
        self.screen.blit(apply_surface, apply_surface.get_rect(center=self.apply_button.center))

    def draw_status_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL_ALT, (0, WINDOW_HEIGHT - STATUS_BAR_HEIGHT, WINDOW_WIDTH, STATUS_BAR_HEIGHT))
        draw_text(self.screen, self.status_message, (12, WINDOW_HEIGHT - 23), self.font_small)

        camera_text = f"Camera: {self.camera_x // TILE_SIZE}, {self.camera_y // TILE_SIZE} | Shift+Click: select topmost"
        camera_surface = self.font_small.render(camera_text, True, MUTED_TEXT)
        self.screen.blit(camera_surface, camera_surface.get_rect(midright=(WINDOW_WIDTH - 12, WINDOW_HEIGHT - 15)))

    @staticmethod
    def wrap_text(text: str, width: int, font: pygame.font.Font) -> list[str]:
        words = str(text).split()
        if not words:
            return [""]

        lines: list[str] = []
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if font.size(test_line)[0] <= width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines


def main() -> int:
    try:
        editor = BloomQuestEditor()
        editor.run()
        return 0
    except Exception as error:
        print("BloomQuest failed to start.")
        print(f"Reason: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
