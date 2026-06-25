# main.py
# run with: python main.py
# path: projects/bloomquest_engine/main.py
# description: First runnable BloomQuest editor prototype with a grid, premade parts palette, four layers, click-to-place editing, and JSON room saving.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, pygame, editor, grid, emoji, json, prototype
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Uses colored tiles and emoji where the active system font supports them. Press Ctrl+S to save and Ctrl+L to load.
# uuid: bc-bloomquest-editor-0001

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pygame


# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
PARTS_FILE = ROOT_DIR / "data" / "parts" / "parts_library.json"
ROOMS_DIR = ROOT_DIR / "data" / "rooms"
ROOM_FILE = ROOMS_DIR / "room_001.json"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60

GRID_COLUMNS = 128
GRID_ROWS = 128
TILE_SIZE = 32

PALETTE_WIDTH = 250
PROPERTIES_WIDTH = 280
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

BACKGROUND = (25, 28, 34)
PANEL = (35, 39, 47)
PANEL_ALT = (43, 48, 58)
TEXT = (235, 238, 244)
MUTED_TEXT = (165, 172, 184)
GRID_LINE = (65, 72, 84)
ACCENT = (110, 190, 130)
SELECTION = (245, 210, 90)
DANGER = (215, 85, 85)


# -----------------------------------------------------------------------------
# Data helpers
# -----------------------------------------------------------------------------


def load_parts_library() -> list[dict[str, Any]]:
    """Load the premade BloomQuest parts library."""
    if not PARTS_FILE.exists():
        raise FileNotFoundError(f"Missing parts library: {PARTS_FILE}")

    with PARTS_FILE.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    parts = payload.get("parts", [])
    if not isinstance(parts, list):
        raise ValueError("parts_library.json must contain a 'parts' list.")

    return parts


def make_blank_room() -> dict[str, Any]:
    """Create a fresh room document using the current engine format."""
    return {
        "format": "bloomquest/room-v0.1",
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
    """Save the current room to a readable JSON file."""
    ROOMS_DIR.mkdir(parents=True, exist_ok=True)
    with ROOM_FILE.open("w", encoding="utf-8") as file_handle:
        json.dump(room, file_handle, indent=2, ensure_ascii=False)


def load_room() -> dict[str, Any]:
    """Load room_001.json if it exists, otherwise return a blank room."""
    if not ROOM_FILE.exists():
        return make_blank_room()

    with ROOM_FILE.open("r", encoding="utf-8") as file_handle:
        room = json.load(file_handle)

    if "layers" not in room:
        room["layers"] = {layer_name: [] for layer_name in LAYER_ORDER}

    for layer_name in LAYER_ORDER:
        room["layers"].setdefault(layer_name, [])

    return room


# -----------------------------------------------------------------------------
# Drawing helpers
# -----------------------------------------------------------------------------


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a broadly available font with emoji fallback where supported."""
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
    """Draw text and return its rectangle."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(topleft=position)
    surface.blit(rendered, rect)
    return rect


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Clamp an integer to a safe range."""
    return max(minimum, min(maximum, value))


# -----------------------------------------------------------------------------
# Editor application
# -----------------------------------------------------------------------------


class BloomQuestEditor:
    """Small first-pass editor proving the BloomQuest architecture."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("BloomQuest Engine v0.1")

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
        self.status_message = "Ready. Choose a part and click the grid."
        self.running = True

    @property
    def selected_part(self) -> dict[str, Any]:
        """Return the currently selected library part."""
        return self.parts[self.selected_part_index]

    def visible_parts(self) -> list[tuple[int, dict[str, Any]]]:
        """Return parts belonging to the active layer."""
        return [
            (index, part)
            for index, part in enumerate(self.parts)
            if part.get("layer") == self.active_layer
        ]

    def run(self) -> None:
        """Run the main editor loop."""
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self) -> None:
        """Handle keyboard and mouse input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event)

            elif event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_x < PALETTE_WIDTH:
                    self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
                elif CANVAS_LEFT <= mouse_x < CANVAS_RIGHT:
                    self.camera_y = clamp(
                        self.camera_y - event.y * TILE_SIZE,
                        0,
                        max(0, GRID_ROWS * TILE_SIZE - CANVAS_HEIGHT),
                    )

    def handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle editor shortcuts."""
        control_down = bool(event.mod & pygame.KMOD_CTRL)

        if event.key == pygame.K_ESCAPE:
            self.running = False

        elif control_down and event.key == pygame.K_s:
            save_room(self.room)
            self.status_message = f"Saved {ROOM_FILE.name}"

        elif control_down and event.key == pygame.K_l:
            self.room = load_room()
            self.selected_instance = None
            self.status_message = f"Loaded {ROOM_FILE.name}"

        elif event.key == pygame.K_DELETE and self.selected_instance is not None:
            self.delete_selected_instance()

        elif event.key == pygame.K_LEFT:
            self.camera_x = max(0, self.camera_x - TILE_SIZE)

        elif event.key == pygame.K_RIGHT:
            self.camera_x = min(
                max(0, GRID_COLUMNS * TILE_SIZE - CANVAS_WIDTH),
                self.camera_x + TILE_SIZE,
            )

        elif event.key == pygame.K_UP:
            self.camera_y = max(0, self.camera_y - TILE_SIZE)

        elif event.key == pygame.K_DOWN:
            self.camera_y = min(
                max(0, GRID_ROWS * TILE_SIZE - CANVAS_HEIGHT),
                self.camera_y + TILE_SIZE,
            )

        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            layer_index = event.key - pygame.K_1
            self.set_active_layer(LAYER_ORDER[layer_index])

    def handle_mouse_down(self, event: pygame.event.Event) -> None:
        """Route clicks to the correct editor area."""
        mouse_x, mouse_y = event.pos

        if mouse_y < TOP_BAR_HEIGHT:
            self.handle_top_bar_click(mouse_x, mouse_y)
            return

        if mouse_x < PALETTE_WIDTH:
            self.handle_palette_click(mouse_x, mouse_y)
            return

        if CANVAS_LEFT <= mouse_x < CANVAS_RIGHT and CANVAS_TOP <= mouse_y < CANVAS_BOTTOM:
            grid_x, grid_y = self.screen_to_grid(mouse_x, mouse_y)

            if not self.grid_position_valid(grid_x, grid_y):
                return

            if event.button == 1:
                self.place_or_select_part(grid_x, grid_y)
            elif event.button == 3:
                self.erase_at(grid_x, grid_y)

    def handle_top_bar_click(self, mouse_x: int, mouse_y: int) -> None:
        """Change active layers using the top bar buttons."""
        button_x = 310
        button_width = 155

        for layer_name in LAYER_ORDER:
            button_rect = pygame.Rect(button_x, 10, button_width, 34)
            if button_rect.collidepoint(mouse_x, mouse_y):
                self.set_active_layer(layer_name)
                return
            button_x += button_width + 8

    def set_active_layer(self, layer_name: str) -> None:
        """Switch the current layer and choose its first available part."""
        self.active_layer = layer_name
        self.selected_instance = None
        self.palette_scroll = 0

        for index, part in enumerate(self.parts):
            if part.get("layer") == layer_name:
                self.selected_part_index = index
                break

        self.status_message = f"Layer: {LAYER_LABELS[layer_name]}"

    def handle_palette_click(self, mouse_x: int, mouse_y: int) -> None:
        """Select a premade part from the palette."""
        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        row_height = 48

        for visible_row, (part_index, part) in enumerate(self.visible_parts()):
            row_rect = pygame.Rect(10, start_y + visible_row * row_height, PALETTE_WIDTH - 20, 42)
            if row_rect.collidepoint(mouse_x, mouse_y):
                self.selected_part_index = part_index
                self.selected_instance = None
                self.status_message = f"Selected {part['name']}"
                return

    def screen_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int]:
        """Convert screen coordinates into room grid coordinates."""
        world_x = mouse_x - CANVAS_LEFT + self.camera_x
        world_y = mouse_y - CANVAS_TOP + self.camera_y
        return world_x // TILE_SIZE, world_y // TILE_SIZE

    def grid_position_valid(self, grid_x: int, grid_y: int) -> bool:
        """Return whether the position is inside the 128 x 128 map."""
        return 0 <= grid_x < GRID_COLUMNS and 0 <= grid_y < GRID_ROWS

    def find_instance_at(self, grid_x: int, grid_y: int, layer_name: str | None = None) -> dict[str, Any] | None:
        """Find the topmost instance occupying one grid cell."""
        layers = [layer_name] if layer_name else list(reversed(LAYER_ORDER))

        for current_layer in layers:
            for instance in reversed(self.room["layers"].get(current_layer, [])):
                if instance.get("x") == grid_x and instance.get("y") == grid_y:
                    return instance

        return None

    def place_or_select_part(self, grid_x: int, grid_y: int) -> None:
        """Place the selected premade part or select an existing matching-layer part."""
        existing = self.find_instance_at(grid_x, grid_y, self.active_layer)
        selected_part = self.selected_part

        if existing and existing.get("part_id") == selected_part.get("id"):
            self.selected_instance = existing
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
        self.status_message = f"Placed {instance['name']} at {grid_x}, {grid_y}"

    def erase_at(self, grid_x: int, grid_y: int) -> None:
        """Erase the active-layer part at a grid position."""
        existing = self.find_instance_at(grid_x, grid_y, self.active_layer)
        if existing is None:
            return

        self.room["layers"][self.active_layer].remove(existing)

        if self.selected_instance is existing:
            self.selected_instance = None

        self.status_message = f"Erased part at {grid_x}, {grid_y}"

    def delete_selected_instance(self) -> None:
        """Delete the currently selected placed instance."""
        if self.selected_instance is None:
            return

        layer_name = self.selected_instance.get("layer", self.active_layer)
        layer_items = self.room["layers"].get(layer_name, [])

        if self.selected_instance in layer_items:
            name = self.selected_instance.get("name", "part")
            layer_items.remove(self.selected_instance)
            self.status_message = f"Deleted {name}"

        self.selected_instance = None

    def draw(self) -> None:
        """Draw the complete editor interface."""
        self.screen.fill(BACKGROUND)
        self.draw_top_bar()
        self.draw_palette()
        self.draw_canvas()
        self.draw_properties_panel()
        self.draw_status_bar()

    def draw_top_bar(self) -> None:
        """Draw the title and layer buttons."""
        pygame.draw.rect(self.screen, PANEL, (0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.1", (16, 13), self.font_large)

        button_x = 310
        button_width = 155

        for layer_name in LAYER_ORDER:
            is_active = layer_name == self.active_layer
            button_color = ACCENT if is_active else PANEL_ALT
            text_color = BACKGROUND if is_active else TEXT
            button_rect = pygame.Rect(button_x, 10, button_width, 34)
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=6)
            label = LAYER_LABELS[layer_name]
            label_surface = self.font_small.render(label, True, text_color)
            label_rect = label_surface.get_rect(center=button_rect.center)
            self.screen.blit(label_surface, label_rect)
            button_x += button_width + 8

    def draw_palette(self) -> None:
        """Draw the premade parts list."""
        palette_rect = pygame.Rect(0, TOP_BAR_HEIGHT, PALETTE_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL, palette_rect)

        draw_text(self.screen, "Premade Parts", (14, TOP_BAR_HEIGHT + 12), self.font_medium)
        draw_text(
            self.screen,
            LAYER_LABELS[self.active_layer],
            (14, TOP_BAR_HEIGHT + 36),
            self.font_small,
            MUTED_TEXT,
        )

        start_y = TOP_BAR_HEIGHT + 62 - self.palette_scroll
        row_height = 48

        for visible_row, (part_index, part) in enumerate(self.visible_parts()):
            row_y = start_y + visible_row * row_height

            if row_y + 42 < TOP_BAR_HEIGHT + 58 or row_y > CANVAS_BOTTOM:
                continue

            is_selected = part_index == self.selected_part_index
            row_color = (72, 83, 78) if is_selected else PANEL_ALT
            row_rect = pygame.Rect(10, row_y, PALETTE_WIDTH - 20, 42)
            pygame.draw.rect(self.screen, row_color, row_rect, border_radius=5)

            emoji = part.get("emoji", "")
            color = tuple(part.get("color", [180, 180, 180]))

            icon_rect = pygame.Rect(16, row_y + 6, 30, 30)
            pygame.draw.rect(self.screen, color, icon_rect, border_radius=4)

            if emoji:
                emoji_surface = self.font_emoji.render(emoji, True, TEXT)
                emoji_rect = emoji_surface.get_rect(center=icon_rect.center)
                self.screen.blit(emoji_surface, emoji_rect)

            draw_text(self.screen, part.get("name", "Part"), (54, row_y + 11), self.font_small)

        pygame.draw.line(
            self.screen,
            GRID_LINE,
            (PALETTE_WIDTH - 1, TOP_BAR_HEIGHT),
            (PALETTE_WIDTH - 1, WINDOW_HEIGHT),
        )

    def draw_canvas(self) -> None:
        """Draw the visible grid and every placed part."""
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
                cell_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, width=1)

        for layer_name in LAYER_ORDER:
            for instance in self.room["layers"].get(layer_name, []):
                self.draw_instance(instance)

        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, GRID_LINE, canvas_rect, width=1)

    def draw_instance(self, instance: dict[str, Any]) -> None:
        """Draw one placed part using its color and emoji."""
        grid_x = int(instance.get("x", 0))
        grid_y = int(instance.get("y", 0))
        screen_x = CANVAS_LEFT + grid_x * TILE_SIZE - self.camera_x
        screen_y = CANVAS_TOP + grid_y * TILE_SIZE - self.camera_y

        if screen_x + TILE_SIZE < CANVAS_LEFT or screen_x > CANVAS_RIGHT:
            return
        if screen_y + TILE_SIZE < CANVAS_TOP or screen_y > CANVAS_BOTTOM:
            return

        cell_rect = pygame.Rect(screen_x + 1, screen_y + 1, TILE_SIZE - 2, TILE_SIZE - 2)
        color = tuple(instance.get("color", [180, 180, 180]))
        pygame.draw.rect(self.screen, color, cell_rect, border_radius=3)

        emoji = instance.get("emoji", "")
        if emoji:
            emoji_surface = self.font_emoji.render(emoji, True, TEXT)
            emoji_rect = emoji_surface.get_rect(center=cell_rect.center)
            self.screen.blit(emoji_surface, emoji_rect)

        if instance is self.selected_instance:
            pygame.draw.rect(self.screen, SELECTION, cell_rect, width=3, border_radius=3)

    def draw_properties_panel(self) -> None:
        """Draw selected-part or selected-instance information."""
        panel_rect = pygame.Rect(CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, WINDOW_HEIGHT - TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL, panel_rect)
        pygame.draw.line(
            self.screen,
            GRID_LINE,
            (CANVAS_RIGHT, TOP_BAR_HEIGHT),
            (CANVAS_RIGHT, WINDOW_HEIGHT),
        )

        draw_text(self.screen, "Properties", (CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 14), self.font_medium)

        target = self.selected_instance if self.selected_instance is not None else self.selected_part
        y = TOP_BAR_HEIGHT + 56

        emoji = target.get("emoji", "")
        name = target.get("name", "Unnamed")

        if emoji:
            draw_text(self.screen, emoji, (CANVAS_RIGHT + 16, y), self.font_large)
            draw_text(self.screen, name, (CANVAS_RIGHT + 54, y + 2), self.font_medium)
        else:
            draw_text(self.screen, name, (CANVAS_RIGHT + 16, y + 2), self.font_medium)

        y += 42
        fields = [
            ("Layer", LAYER_LABELS.get(target.get("layer", self.active_layer), "Unknown")),
            ("ID", target.get("instance_id", target.get("id", target.get("part_id", "-")))),
            ("Solid", str(target.get("solid", False))),
        ]

        if self.selected_instance is not None:
            fields.extend(
                [
                    ("Grid X", str(target.get("x", 0))),
                    ("Grid Y", str(target.get("y", 0))),
                    ("Enabled", str(target.get("enabled", True))),
                ]
            )

        for label, value in fields:
            draw_text(self.screen, label, (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            draw_text(self.screen, value, (CANVAS_RIGHT + 105, y), self.font_small)
            y += 26

        y += 8
        draw_text(self.screen, "Description", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
        y += 24

        description = str(target.get("description", ""))
        wrapped_lines = self.wrap_text(description, PROPERTIES_WIDTH - 32, self.font_small)

        for line in wrapped_lines[:5]:
            draw_text(self.screen, line, (CANVAS_RIGHT + 16, y), self.font_small)
            y += 21

        action = target.get("action")
        if action:
            y += 12
            draw_text(self.screen, "Action", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
            y += 24

            for key, value in action.items():
                action_line = f"{key}: {value}"
                for line in self.wrap_text(action_line, PROPERTIES_WIDTH - 32, self.font_small):
                    draw_text(self.screen, line, (CANVAS_RIGHT + 16, y), self.font_small)
                    y += 20

        y = WINDOW_HEIGHT - 150
        draw_text(self.screen, "Controls", (CANVAS_RIGHT + 16, y), self.font_small, MUTED_TEXT)
        y += 24
        draw_text(self.screen, "Left click: place/select", (CANVAS_RIGHT + 16, y), self.font_small)
        y += 21
        draw_text(self.screen, "Right click: erase", (CANVAS_RIGHT + 16, y), self.font_small)
        y += 21
        draw_text(self.screen, "Arrows: pan map", (CANVAS_RIGHT + 16, y), self.font_small)
        y += 21
        draw_text(self.screen, "Ctrl+S save / Ctrl+L load", (CANVAS_RIGHT + 16, y), self.font_small)

    def draw_status_bar(self) -> None:
        """Draw the bottom status bar."""
        bar_rect = pygame.Rect(0, WINDOW_HEIGHT - STATUS_BAR_HEIGHT, WINDOW_WIDTH, STATUS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_ALT, bar_rect)

        draw_text(self.screen, self.status_message, (12, WINDOW_HEIGHT - 23), self.font_small)

        camera_text = f"Camera: {self.camera_x // TILE_SIZE}, {self.camera_y // TILE_SIZE}"
        camera_surface = self.font_small.render(camera_text, True, MUTED_TEXT)
        camera_rect = camera_surface.get_rect(midright=(WINDOW_WIDTH - 12, WINDOW_HEIGHT - 15))
        self.screen.blit(camera_surface, camera_rect)

    @staticmethod
    def wrap_text(text: str, width: int, font: pygame.font.Font) -> list[str]:
        """Wrap text to fit a pixel width."""
        words = text.split()
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


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------


def main() -> int:
    """Start BloomQuest and report readable startup errors."""
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
