# bloomquest_app.py
# run with: imported by main.py
# path: projects/bloomquest_engine/editor/bloomquest_app.py
# description: BloomQuest v0.4 editor with rooms, help menu, properties, saving, and multi-room play testing.
# version: 0.4.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, editor, rooms, menu, manual, glossary, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Ctrl+S saves. F5 plays. Rooms and Help are built into the top menu.
# uuid: bc-bloomquest-app-0004

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pygame

from engine.room_manager import RoomManager
from engine.world_play import WorldPlay

ROOT_DIR = Path(__file__).resolve().parents[1]
PARTS_FILE = ROOT_DIR / "data" / "parts" / "parts_library.json"
ROOMS_DIR = ROOT_DIR / "data" / "rooms"
DOCS_DIR = ROOT_DIR / "docs"

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


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ("Segoe UI Emoji", "Segoe UI Symbol", "Arial Unicode MS", "DejaVu Sans", None):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)


def draw_text(surface: pygame.Surface, text: Any, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int] = TEXT) -> pygame.Rect:
    image = font.render(str(text), True, color)
    rect = image.get_rect(topleft=(x, y))
    surface.blit(image, rect)
    return rect


def safe_int(value: Any, fallback: int = 0) -> int:
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


class BloomQuestApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("BloomQuest Engine v0.4")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = get_font(16)
        self.font_medium = get_font(20)
        self.font_large = get_font(26, bold=True)
        self.font_title = get_font(34, bold=True)
        self.font_emoji = get_font(23)

        with PARTS_FILE.open("r", encoding="utf-8") as handle:
            self.parts = json.load(handle).get("parts", [])

        self.room_manager = RoomManager(ROOMS_DIR, GRID_COLUMNS, GRID_ROWS, TILE_SIZE)
        room_ids = self.room_manager.list_room_ids()
        self.current_room_id = room_ids[0] if room_ids else "room_001"
        self.room = self.room_manager.load(self.current_room_id)

        self.active_layer = "map"
        self.selected_part_index = 0
        self.selected_instance: dict[str, Any] | None = None
        self.fields: list[TextField] = []
        self.field_by_key: dict[str, TextField] = {}
        self.camera_x = 0
        self.camera_y = 0
        self.palette_scroll = 0
        self.properties_scroll = 0
        self.status_message = "Ready. Build a room or open Help."
        self.mode = "edit"
        self.overlay: str | None = None
        self.overlay_scroll = 0
        self.world_play: WorldPlay | None = None
        self.running = True

        self.play_button = pygame.Rect(WINDOW_WIDTH - 96, 10, 78, 34)
        self.rooms_button = pygame.Rect(WINDOW_WIDTH - 270, 10, 78, 34)
        self.help_button = pygame.Rect(WINDOW_WIDTH - 184, 10, 78, 34)
        self.apply_button = pygame.Rect(0, 0, 0, 0)
        self.action_button = pygame.Rect(0, 0, 0, 0)
        self.overlay_buttons: list[tuple[str, pygame.Rect]] = []

    @property
    def selected_part(self) -> dict[str, Any]:
        return self.parts[self.selected_part_index]

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
                self.handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event)
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_wheel(event)

    def handle_key(self, event: pygame.event.Event) -> None:
        if self.mode == "play":
            if self.world_play and not self.world_play.handle_key(event):
                self.exit_play_mode()
            return

        if self.overlay:
            if event.key == pygame.K_ESCAPE:
                self.overlay = None
                self.overlay_scroll = 0
            return

        active_field = next((field for field in self.fields if field.active), None)
        if active_field:
            active_field.handle_key(event)
            return

        control = bool(event.mod & pygame.KMOD_CTRL)
        if event.key == pygame.K_F5:
            self.enter_play_mode()
        elif event.key == pygame.K_F1:
            self.overlay = "help"
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif control and event.key == pygame.K_s:
            self.save_current_room()
        elif control and event.key == pygame.K_l:
            self.room = self.room_manager.load(self.current_room_id)
            self.clear_selection()
            self.status_message = f"Reloaded {self.current_room_id}"
        elif event.key == pygame.K_DELETE:
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
            self.set_layer(LAYER_ORDER[event.key - pygame.K_1])

    def handle_click(self, event: pygame.event.Event) -> None:
        x, y = event.pos
        if self.mode == "play":
            return

        if self.overlay:
            self.handle_overlay_click(x, y)
            return

        if self.play_button.collidepoint(x, y):
            self.enter_play_mode()
            return
        if self.rooms_button.collidepoint(x, y):
            self.overlay = "rooms"
            return
        if self.help_button.collidepoint(x, y):
            self.overlay = "help"
            return

        for field in self.fields:
            field.active = field.rect.collidepoint(x, y)

        if self.apply_button.collidepoint(x, y):
            self.apply_properties()
            return
        if self.action_button.collidepoint(x, y):
            self.cycle_action()
            return

        if y < TOP_BAR_HEIGHT:
            button_x = 280
            for layer in LAYER_ORDER:
                rect = pygame.Rect(button_x, 10, 140, 34)
                if rect.collidepoint(x, y):
                    self.set_layer(layer)
                    return
                button_x += 146

        if x < PALETTE_WIDTH:
            start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
            for row, (index, part) in enumerate(self.visible_parts()):
                rect = pygame.Rect(10, start_y + row * 48, PALETTE_WIDTH - 20, 42)
                if rect.collidepoint(x, y):
                    self.selected_part_index = index
                    self.clear_selection()
                    self.status_message = f"Selected {part.get('name', 'Part')}"
                    return

        if CANVAS_LEFT <= x < CANVAS_RIGHT and CANVAS_TOP <= y < CANVAS_BOTTOM:
            gx = (x - CANVAS_LEFT + self.camera_x) // TILE_SIZE
            gy = (y - CANVAS_TOP + self.camera_y) // TILE_SIZE
            if event.button == 1:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.select_topmost(gx, gy)
                else:
                    self.place_or_select(gx, gy)
            elif event.button == 3:
                self.erase_at(gx, gy)

    def handle_wheel(self, event: pygame.event.Event) -> None:
        if self.overlay:
            self.overlay_scroll = max(0, self.overlay_scroll - event.y * 30)
            return
        x, _ = pygame.mouse.get_pos()
        if x < PALETTE_WIDTH:
            self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
        elif x >= CANVAS_RIGHT:
            self.properties_scroll = max(0, self.properties_scroll - event.y * 34)
        else:
            self.camera_y = max(0, self.camera_y - event.y * TILE_SIZE)

    def visible_parts(self) -> list[tuple[int, dict[str, Any]]]:
        return [(index, part) for index, part in enumerate(self.parts) if part.get("layer") == self.active_layer]

    def set_layer(self, layer: str) -> None:
        self.active_layer = layer
        self.clear_selection()
        for index, part in enumerate(self.parts):
            if part.get("layer") == layer:
                self.selected_part_index = index
                break
        self.status_message = f"Layer: {LAYER_LABELS[layer]}"

    def save_current_room(self) -> None:
        self.room_manager.save(self.room)
        self.status_message = f"Saved {self.current_room_id}"

    def switch_room(self, room_id: str) -> None:
        self.save_current_room()
        self.current_room_id = room_id
        self.room = self.room_manager.load(room_id)
        self.camera_x = 0
        self.camera_y = 0
        self.clear_selection()
        self.overlay = None
        self.status_message = f"Opened {room_id}"

    def find_at(self, gx: int, gy: int, layer: str | None = None) -> dict[str, Any] | None:
        layers = [layer] if layer else list(reversed(LAYER_ORDER))
        for current_layer in layers:
            for item in reversed(self.room["layers"].get(current_layer, [])):
                if item.get("x") == gx and item.get("y") == gy:
                    return item
        return None

    def place_or_select(self, gx: int, gy: int) -> None:
        if not (0 <= gx < GRID_COLUMNS and 0 <= gy < GRID_ROWS):
            return
        existing = self.find_at(gx, gy, self.active_layer)
        selected = self.selected_part
        if existing and existing.get("part_id") == selected.get("id"):
            self.selected_instance = existing
            self.build_fields()
            self.status_message = f"Selected {existing.get('name', 'Part')}"
            return
        if existing:
            self.room["layers"][self.active_layer].remove(existing)
        number = len(self.room["layers"][self.active_layer]) + 1
        item = {
            "instance_id": f"{selected['id']}_{number:04d}",
            "part_id": selected["id"],
            "emoji": selected.get("emoji", ""),
            "name": selected.get("name", selected["id"]),
            "description": selected.get("description", ""),
            "layer": selected.get("layer", self.active_layer),
            "x": gx,
            "y": gy,
            "color": selected.get("color", [180, 180, 180]),
            "solid": selected.get("solid", False),
            "enabled": True,
        }
        for key in ("action", "health", "damage"):
            if key in selected:
                item[key] = deepcopy(selected[key])
        self.room["layers"][self.active_layer].append(item)
        self.selected_instance = item
        self.build_fields()
        self.status_message = f"Placed {item['name']} at {gx}, {gy}"

    def select_topmost(self, gx: int, gy: int) -> None:
        item = self.find_at(gx, gy)
        if item:
            self.selected_instance = item
            self.active_layer = item.get("layer", self.active_layer)
            self.build_fields()
            self.status_message = f"Selected {item.get('name', 'Part')}"

    def erase_at(self, gx: int, gy: int) -> None:
        item = self.find_at(gx, gy, self.active_layer)
        if item:
            self.room["layers"][self.active_layer].remove(item)
            if item is self.selected_instance:
                self.clear_selection()

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
            TextField("description", "Description", target.get("description", ""), True),
            TextField("text", "Text / Dialogue", action.get("text", ""), True),
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

    def cycle_action(self) -> None:
        if not self.selected_instance:
            return
        action = self.selected_instance.setdefault("action", {})
        current = action.get("type", "none")
        try:
            index = ACTION_TYPES.index(current)
        except ValueError:
            index = 0
        action["type"] = ACTION_TYPES[(index + 1) % len(ACTION_TYPES)]
        self.status_message = f"Action: {action['type']}"

    def apply_properties(self) -> None:
        if not self.selected_instance:
            return
        target = self.selected_instance
        target["name"] = self.field_by_key["name"].value.strip() or "Part"
        target["description"] = self.field_by_key["description"].value.strip()
        target["health"] = safe_int(self.field_by_key["health"].value, target.get("health", 0))
        target["damage"] = safe_int(self.field_by_key["damage"].value, target.get("damage", 0))
        action = target.setdefault("action", {})
        for key in ("text", "counter", "target_room"):
            action[key] = self.field_by_key[key].value.strip()
        for key in ("amount", "target_x", "target_y", "seconds"):
            action[key] = safe_int(self.field_by_key[key].value, action.get(key, 0))
        self.status_message = f"Updated {target['name']}"

    def enter_play_mode(self) -> None:
        self.save_current_room()
        has_player = any(item.get("part_id") == "player" for item in self.room["layers"].get("actors", []))
        if not has_player:
            self.status_message = "Place a Player in this room first."
            return
        self.world_play = WorldPlay(self.room_manager, self.current_room_id, TILE_SIZE, pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT))
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.4 — PLAY MODE")

    def exit_play_mode(self) -> None:
        self.mode = "edit"
        self.world_play = None
        self.status_message = "Returned to Edit Mode. Test changes discarded."
        pygame.display.set_caption("BloomQuest Engine v0.4")

    def handle_overlay_click(self, x: int, y: int) -> None:
        for name, rect in self.overlay_buttons:
            if rect.collidepoint(x, y):
                if name == "close":
                    self.overlay = None
                elif name == "new_room":
                    room = self.room_manager.create()
                    self.switch_room(room["room_id"])
                elif name == "duplicate_room":
                    room = self.room_manager.duplicate(self.room)
                    self.switch_room(room["room_id"])
                elif name.startswith("open:"):
                    self.switch_room(name.split(":", 1)[1])
                elif name in ("manual", "directions", "glossary"):
                    self.overlay = name
                    self.overlay_scroll = 0
                return

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.draw_top_bar()
        if self.mode == "play" and self.world_play:
            self.draw_play_mode()
        else:
            self.draw_palette()
            self.draw_canvas()
            self.draw_properties()
        self.draw_status()
        if self.overlay:
            self.draw_overlay()

    def draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
        title = f"BloomQuest v0.4 — {self.current_room_id}"
        draw_text(self.screen, title, 14, 13, self.font_large)
        if self.mode == "edit":
            x = 280
            for layer in LAYER_ORDER:
                rect = pygame.Rect(x, 10, 140, 34)
                active = layer == self.active_layer
                pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
                image = self.font_small.render(LAYER_LABELS[layer], True, BACKGROUND if active else TEXT)
                self.screen.blit(image, image.get_rect(center=rect.center))
                x += 146
            for rect, label in ((self.rooms_button, "Rooms"), (self.help_button, "Help"), (self.play_button, "▶ Play")):
                pygame.draw.rect(self.screen, ACCENT if label == "▶ Play" else PANEL_ALT, rect, border_radius=6)
                image = self.font_small.render(label, True, BACKGROUND if label == "▶ Play" else TEXT)
                self.screen.blit(image, image.get_rect(center=rect.center))

    def draw_palette(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Premade Parts", 14, TOP_BAR_HEIGHT + 12, self.font_medium)
        draw_text(self.screen, LAYER_LABELS[self.active_layer], 14, TOP_BAR_HEIGHT + 36, self.font_small, MUTED_TEXT)
        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        for row, (index, part) in enumerate(self.visible_parts()):
            y = start_y + row * 48
            if y + 42 < TOP_BAR_HEIGHT or y > CANVAS_BOTTOM:
                continue
            rect = pygame.Rect(10, y, PALETTE_WIDTH - 20, 42)
            pygame.draw.rect(self.screen, (72, 83, 78) if index == self.selected_part_index else PANEL_ALT, rect, border_radius=5)
            icon = pygame.Rect(16, y + 6, 30, 30)
            pygame.draw.rect(self.screen, tuple(part.get("color", [180, 180, 180])), icon, border_radius=4)
            emoji = part.get("emoji", "")
            if emoji:
                image = self.font_emoji.render(emoji, True, TEXT)
                self.screen.blit(image, image.get_rect(center=icon.center))
            draw_text(self.screen, part.get("name", "Part"), 54, y + 11, self.font_small)

    def draw_canvas(self) -> None:
        rect = pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, CANVAS_COLOR, rect)
        self.screen.set_clip(rect)
        start_x = self.camera_x // TILE_SIZE
        start_y = self.camera_y // TILE_SIZE
        for gy in range(start_y, start_y + CANVAS_HEIGHT // TILE_SIZE + 2):
            for gx in range(start_x, start_x + CANVAS_WIDTH // TILE_SIZE + 2):
                sx = CANVAS_LEFT + gx * TILE_SIZE - self.camera_x
                sy = CANVAS_TOP + gy * TILE_SIZE - self.camera_y
                pygame.draw.rect(self.screen, GRID_LINE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)
        for layer in LAYER_ORDER:
            for item in self.room["layers"].get(layer, []):
                self.draw_item(self.screen, item, self.camera_x, self.camera_y, True)
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, rect, 1)

    def draw_item(self, surface: pygame.Surface, item: dict[str, Any], camera_x: int, camera_y: int, show_selection: bool) -> None:
        sx = CANVAS_LEFT + int(item.get("x", 0)) * TILE_SIZE - camera_x
        sy = CANVAS_TOP + int(item.get("y", 0)) * TILE_SIZE - camera_y
        if sx + TILE_SIZE < CANVAS_LEFT or sx > CANVAS_RIGHT or sy + TILE_SIZE < CANVAS_TOP or sy > CANVAS_BOTTOM:
            return
        rect = pygame.Rect(sx + 1, sy + 1, TILE_SIZE - 2, TILE_SIZE - 2)
        pygame.draw.rect(surface, tuple(item.get("color", [180, 180, 180])), rect, border_radius=3)
        emoji = item.get("emoji", "")
        if emoji:
            image = self.font_emoji.render(emoji, True, TEXT)
            surface.blit(image, image.get_rect(center=rect.center))
        if show_selection and item is self.selected_instance:
            pygame.draw.rect(surface, SELECTION, rect, 3, border_radius=3)

    def draw_properties(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Properties", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 14, self.font_medium)
        if not self.selected_instance:
            draw_text(self.screen, "Place a part, then click it again", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 64, self.font_small, MUTED_TEXT)
            draw_text(self.screen, "to edit its fields.", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 88, self.font_small, MUTED_TEXT)
            return
        y = TOP_BAR_HEIGHT + 52 - self.properties_scroll
        target = self.selected_instance
        draw_text(self.screen, target.get("emoji", ""), CANVAS_RIGHT + 16, y, self.font_large)
        draw_text(self.screen, target.get("name", "Part"), CANVAS_RIGHT + 54, y + 2, self.font_medium)
        y += 48
        draw_text(self.screen, "Action Type", CANVAS_RIGHT + 16, y, self.font_small, MUTED_TEXT)
        y += 22
        self.action_button = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, 34)
        pygame.draw.rect(self.screen, PANEL_ALT, self.action_button, border_radius=5)
        image = self.font_small.render(target.get("action", {}).get("type", "none"), True, TEXT)
        self.screen.blit(image, image.get_rect(center=self.action_button.center))
        y += 48
        for field in self.fields:
            draw_text(self.screen, field.label, CANVAS_RIGHT + 16, y, self.font_small, MUTED_TEXT)
            y += 21
            height = 54 if field.multiline else 34
            field.rect = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, height)
            pygame.draw.rect(self.screen, (52, 61, 72) if field.active else FIELD, field.rect, border_radius=5)
            pygame.draw.rect(self.screen, ACCENT if field.active else GRID_LINE, field.rect, 2, border_radius=5)
            draw_text(self.screen, field.value[-70:], field.rect.x + 7, field.rect.y + 7, self.font_small)
            y += height + 11
        self.apply_button = pygame.Rect(CANVAS_RIGHT + 16, y + 4, PROPERTIES_WIDTH - 32, 40)
        pygame.draw.rect(self.screen, ACCENT, self.apply_button, border_radius=6)
        image = self.font_small.render("Apply Changes", True, BACKGROUND)
        self.screen.blit(image, image.get_rect(center=self.apply_button.center))

    def draw_play_mode(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "PLAY MODE", 18, TOP_BAR_HEIGHT + 18, self.font_medium)
        draw_text(self.screen, "WASD / Arrows", 18, TOP_BAR_HEIGHT + 62, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "E = interact", 18, TOP_BAR_HEIGHT + 86, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Esc = return", 18, TOP_BAR_HEIGHT + 110, self.font_small, MUTED_TEXT)
        pygame.draw.rect(self.screen, PANEL, (CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT))
        draw_text(self.screen, "Session", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 18, self.font_medium)
        if self.world_play:
            colors = {"canvas": CANVAS_COLOR, "grid": GRID_LINE, "panel": PANEL, "text": TEXT, "accent": ACCENT}
            fonts = {"medium": self.font_medium}
            self.world_play.draw(self.screen, self.draw_item, colors, fonts)
            y = TOP_BAR_HEIGHT + 62
            draw_text(self.screen, f"Room: {self.world_play.room_id}", CANVAS_RIGHT + 16, y, self.font_small)
            y += 28
            for key, value in self.world_play.counters.items():
                draw_text(self.screen, f"{key}: {value}", CANVAS_RIGHT + 16, y, self.font_small)
                y += 24
            self.status_message = self.world_play.status

    def draw_status(self) -> None:
        pygame.draw.rect(self.screen, PANEL_ALT, (0, WINDOW_HEIGHT - STATUS_BAR_HEIGHT, WINDOW_WIDTH, STATUS_BAR_HEIGHT))
        draw_text(self.screen, self.status_message, 12, WINDOW_HEIGHT - 23, self.font_small)
        right = "F1 Help | F5 Play | Ctrl+S Save" if self.mode == "edit" else "Esc Return to Edit"
        image = self.font_small.render(right, True, MUTED_TEXT)
        self.screen.blit(image, image.get_rect(midright=(WINDOW_WIDTH - 12, WINDOW_HEIGHT - 15)))

    def draw_overlay(self) -> None:
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))
        box = pygame.Rect(170, 90, WINDOW_WIDTH - 340, WINDOW_HEIGHT - 180)
        pygame.draw.rect(self.screen, PANEL, box, border_radius=10)
        pygame.draw.rect(self.screen, ACCENT, box, 2, border_radius=10)
        self.overlay_buttons = []

        close_rect = pygame.Rect(box.right - 92, box.y + 16, 70, 34)
        pygame.draw.rect(self.screen, PANEL_ALT, close_rect, border_radius=5)
        image = self.font_small.render("Close", True, TEXT)
        self.screen.blit(image, image.get_rect(center=close_rect.center))
        self.overlay_buttons.append(("close", close_rect))

        if self.overlay == "rooms":
            self.draw_rooms_overlay(box)
        elif self.overlay == "help":
            self.draw_help_menu(box)
        elif self.overlay in ("manual", "directions", "glossary"):
            self.draw_help_page(box, self.overlay)

    def draw_rooms_overlay(self, box: pygame.Rect) -> None:
        draw_text(self.screen, "Rooms", box.x + 24, box.y + 18, self.font_title)
        new_rect = pygame.Rect(box.x + 24, box.y + 72, 150, 38)
        duplicate_rect = pygame.Rect(box.x + 184, box.y + 72, 180, 38)
        for name, rect, label in (("new_room", new_rect, "+ New Room"), ("duplicate_room", duplicate_rect, "Duplicate Current")):
            pygame.draw.rect(self.screen, ACCENT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND)
            self.screen.blit(image, image.get_rect(center=rect.center))
            self.overlay_buttons.append((name, rect))

        y = box.y + 132 - self.overlay_scroll
        for room_id in self.room_manager.list_room_ids():
            rect = pygame.Rect(box.x + 24, y, box.width - 48, 44)
            pygame.draw.rect(self.screen, (72, 83, 78) if room_id == self.current_room_id else PANEL_ALT, rect, border_radius=5)
            room = self.room_manager.load(room_id)
            draw_text(self.screen, f"{room_id}  —  {room.get('name', room_id)}", rect.x + 12, rect.y + 11, self.font_small)
            self.overlay_buttons.append((f"open:{room_id}", rect))
            y += 52

    def draw_help_menu(self, box: pygame.Rect) -> None:
        draw_text(self.screen, "BloomQuest Help", box.x + 24, box.y + 18, self.font_title)
        draw_text(self.screen, "The engine includes its own manual, directions, and glossary.", box.x + 24, box.y + 70, self.font_medium, MUTED_TEXT)
        y = box.y + 126
        for name, label, note in (
            ("manual", "Manual", "Full controls, rooms, actions, and saving."),
            ("directions", "Directions", "Fast step-by-step building instructions."),
            ("glossary", "Glossary", "Plain-language meanings for engine terms."),
        ):
            rect = pygame.Rect(box.x + 24, y, box.width - 48, 72)
            pygame.draw.rect(self.screen, PANEL_ALT, rect, border_radius=7)
            draw_text(self.screen, label, rect.x + 16, rect.y + 11, self.font_medium)
            draw_text(self.screen, note, rect.x + 16, rect.y + 39, self.font_small, MUTED_TEXT)
            self.overlay_buttons.append((name, rect))
            y += 84

    def draw_help_page(self, box: pygame.Rect, page: str) -> None:
        titles = {"manual": "Manual", "directions": "Directions", "glossary": "Glossary"}
        draw_text(self.screen, titles[page], box.x + 24, box.y + 18, self.font_title)
        content = self.help_content(page)
        y = box.y + 76 - self.overlay_scroll
        for line in content:
            if y > box.y + 56 and y < box.bottom - 20:
                color = ACCENT if line.startswith("##") else TEXT
                font = self.font_medium if line.startswith("##") else self.font_small
                clean = line.replace("## ", "")
                draw_text(self.screen, clean, box.x + 28, y, font, color)
            y += 28 if line.startswith("##") else 22

    def help_content(self, page: str) -> list[str]:
        if page == "directions":
            return [
                "## Build a Room",
                "1. Choose one of the four layers.",
                "2. Choose a premade part on the left.",
                "3. Left-click the grid to place it.",
                "4. Click it again to edit its properties.",
                "5. Press Apply Changes, then Ctrl+S.",
                "## Test the Game",
                "6. Place one Player on Enemies / Player.",
                "7. Add walls, coins, signs, and a door.",
                "8. Press F5 or click Play.",
                "9. Move with WASD or arrows. Press E to interact.",
                "## Connect Rooms",
                "10. Open Rooms and create room_002.",
                "11. Give a door Target Room room_002 and Target X/Y.",
                "12. Add a return door in room_002.",
            ]
        if page == "glossary":
            return [
                "## Part", "A reusable premade game piece.",
                "## Instance", "One placed copy of a part.",
                "## Room", "One saved map. Doors connect rooms.",
                "## Layer", "A category controlling which parts are edited.",
                "## Property", "A name, text, number, or setting belonging to a part.",
                "## Action", "A premade behavior such as show_text or teleport.",
                "## Counter", "A number such as health, coins, score, or keys.",
                "## Solid", "Blocks player movement.",
                "## Trigger", "The condition that starts an action.",
                "## Play Mode", "A temporary game test that does not alter editor data.",
            ]
        return [
            "## Editor Controls",
            "Left click: place or select the active-layer part.",
            "Shift + left click: select the topmost part.",
            "Right click: erase the active-layer part.",
            "Arrow keys: move the editor camera.",
            "Mouse wheel: scroll the panel under the pointer.",
            "Ctrl+S: save. Ctrl+L: reload. Delete: remove selected.",
            "F1: open Help. F5: enter Play Mode.",
            "## Play Controls",
            "WASD or arrows: move. E: interact. Esc: return.",
            "## Layers",
            "Map: terrain, water, walls, floors, and paths.",
            "Scene Objects: trees, doors, signs, chests, and furniture.",
            "Enemies / Player: player, NPCs, enemies, and bosses.",
            "Weapons / Effects: weapons, projectiles, and visual effects.",
            "## Doors",
            "Set Action Type to teleport.",
            "Enter Target Room such as room_002.",
            "Enter Target X and Target Y for the arrival cell.",
            "## Saving",
            "Rooms are readable JSON files inside data/rooms.",
            "Play Mode uses copies, so testing does not damage room files.",
        ]
