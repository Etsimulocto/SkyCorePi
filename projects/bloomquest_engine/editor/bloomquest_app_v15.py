# bloomquest_app_v15.py
# run with: imported by bloomquest_v15.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v15.py
# description: Adds a visual Maps menu for seeded Forest, Village, Dungeon, Cave, Maze, and Arena generation.
# version: 0.15.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, generator, maps, templates, seed, preview, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Generation always creates a new room and never overwrites the current room.
# uuid: bc-bloomquest-app-0015

from __future__ import annotations

import random

import pygame

from editor.bloomquest_app import BACKGROUND, MUTED_TEXT, PANEL_ALT, TEXT, TOP_BAR_HEIGHT
from editor.bloomquest_app_v142 import BloomQuestAppV142
from editor.bloomquest_app_v14 import dynamic_draw_text
from engine.map_generator_v15 import BloomQuestMapGenerator


class BloomQuestAppV15(BloomQuestAppV142):
    """BloomQuest v0.15 with premade and random room generation."""

    STYLE_INFO = {
        "forest": ("Forest", "Trees, flowers, rocks, and fireflies"),
        "village": ("Village", "Roads, houses, flowers, and a villager"),
        "dungeon": ("Dungeon", "Connected chambers, torches, runes, and enemies"),
        "cave": ("Cave", "Rock formations, puddles, mushrooms, and bones"),
        "maze": ("Maze", "Connected corridors with treasure and enemies"),
        "arena": ("Arena", "Open combat room with obstacles and extra enemies"),
    }

    def __init__(self) -> None:
        super().__init__()
        self.maps_button = pygame.Rect(1090, 10, 88, 34)
        self.settings_button = pygame.Rect(1184, 10, 84, 34)
        self.play_button = pygame.Rect(1274, 10, 80, 34)

        self.generator_style = "forest"
        self.generator_seed = 825
        self.generator_width = 24
        self.generator_height = 20
        self.generator_buttons: dict[str, pygame.Rect] = {}
        self.generator_style_rects: list[tuple[str, pygame.Rect]] = []
        self.generator_preview: dict | None = None
        self.rebuild_generator_preview()

        pygame.display.set_caption("BloomQuest Engine v0.15 — Map Generator")
        self.status_message = "Maps menu ready: premade templates and seeded random generation."

    def rebuild_generator_preview(self) -> None:
        generator = BloomQuestMapGenerator(self.parts)
        self.generator_preview = generator.generate(
            "room_preview",
            self.generator_style,
            self.generator_seed,
            self.generator_width,
            self.generator_height,
        )

    def randomize_seed(self) -> None:
        self.generator_seed = random.SystemRandom().randint(1, 999999)
        self.rebuild_generator_preview()
        self.status_message = f"New generator seed: {self.generator_seed}"

    def generate_new_room(self) -> None:
        room_id = self.room_manager.next_room_id()
        generator = BloomQuestMapGenerator(self.parts)
        room = generator.generate(
            room_id,
            self.generator_style,
            self.generator_seed,
            self.generator_width,
            self.generator_height,
        )
        self.room_manager.save(room)
        self.switch_room(room_id)
        self.overlay = None
        self.status_message = f"Generated {self.generator_style.title()} room {room_id} with seed {self.generator_seed}"

    def handle_click(self, event: pygame.event.Event) -> None:
        if self.overlay == "map_generator":
            self.handle_generator_click(event.pos)
            return

        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            if self.maps_button.collidepoint(event.pos):
                self.overlay = "map_generator"
                self.rebuild_generator_preview()
                return

        super().handle_click(event)

    def handle_generator_click(self, position: tuple[int, int]) -> None:
        for style, rect in self.generator_style_rects:
            if rect.collidepoint(position):
                self.generator_style = style
                self.rebuild_generator_preview()
                self.status_message = f"Map style: {style.title()}"
                return

        actions = {
            "new_seed": self.randomize_seed,
            "generate": self.generate_new_room,
        }
        for name, action in actions.items():
            rect = self.generator_buttons.get(name, pygame.Rect(0, 0, 0, 0))
            if rect.collidepoint(position):
                action()
                return

        if self.generator_buttons.get("close", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
            self.overlay = None

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        if self.mode != "edit":
            return

        pygame.draw.rect(self.screen, self.theme_rgb["panel_alt"], self.maps_button, border_radius=6)
        image = self.font_small.render("Maps", True, self.theme_rgb["text"])
        self.screen.blit(image, image.get_rect(center=self.maps_button.center))

        pygame.draw.rect(self.screen, self.theme_rgb["panel_alt"], self.settings_button, border_radius=6)
        image = self.font_small.render("Settings", True, self.theme_rgb["text"])
        self.screen.blit(image, image.get_rect(center=self.settings_button.center))

        pygame.draw.rect(self.screen, self.theme_rgb["accent"], self.play_button, border_radius=6)
        image = self.font_small.render("▶ Play", True, self.theme_rgb["background"])
        self.screen.blit(image, image.get_rect(center=self.play_button.center))

    def draw_overlay(self) -> None:
        if self.overlay != "map_generator":
            super().draw_overlay()
            return
        self.draw_generator_overlay()

    def draw_generator_overlay(self) -> None:
        shade = pygame.Surface(self.logical_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))

        box = pygame.Rect(110, 60, 1140, 720)
        pygame.draw.rect(self.screen, self.theme_rgb["panel"], box, border_radius=10)
        pygame.draw.rect(self.screen, self.theme_rgb["frame"], box, 3, border_radius=10)

        dynamic_draw_text(self.screen, "Premade & Random Map Generator", box.x + 24, box.y + 18, self.font_title, self.theme_rgb["text"])
        dynamic_draw_text(
            self.screen,
            "Choose a template. The seed changes the layout, enemies, decorations, treasure, and starting weapon.",
            box.x + 26,
            box.y + 58,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        self.generator_style_rects = []
        left_x = box.x + 26
        start_y = box.y + 96
        for index, (style, (title, description)) in enumerate(self.STYLE_INFO.items()):
            rect = pygame.Rect(left_x, start_y + index * 78, 390, 68)
            selected = style == self.generator_style
            pygame.draw.rect(self.screen, self.theme_rgb["accent"] if selected else self.theme_rgb["panel_alt"], rect, border_radius=7)
            pygame.draw.rect(self.screen, self.theme_rgb["frame"] if selected else self.theme_rgb["grid"], rect, 2, border_radius=7)
            foreground = self.theme_rgb["background"] if selected else self.theme_rgb["text"]
            secondary = self.theme_rgb["background"] if selected else self.theme_rgb["muted_text"]
            dynamic_draw_text(self.screen, title, rect.x + 14, rect.y + 10, self.font_medium, foreground)
            dynamic_draw_text(self.screen, description, rect.x + 14, rect.y + 38, self.font_small, secondary)
            self.generator_style_rects.append((style, rect))

        preview_box = pygame.Rect(box.x + 450, box.y + 104, 650, 480)
        pygame.draw.rect(self.screen, self.theme_rgb["canvas"], preview_box, border_radius=8)
        pygame.draw.rect(self.screen, self.theme_rgb["frame"], preview_box, 2, border_radius=8)
        self.draw_generator_preview(preview_box)

        dynamic_draw_text(
            self.screen,
            f"Seed: {self.generator_seed}",
            preview_box.x,
            preview_box.bottom + 18,
            self.font_medium,
            self.theme_rgb["text"],
        )
        dynamic_draw_text(
            self.screen,
            f"Room size: {self.generator_width} × {self.generator_height} tiles",
            preview_box.x + 220,
            preview_box.bottom + 21,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

        new_seed = pygame.Rect(preview_box.x, preview_box.bottom + 58, 160, 40)
        generate = pygame.Rect(preview_box.x + 176, preview_box.bottom + 58, 240, 40)
        close = pygame.Rect(preview_box.right - 110, preview_box.bottom + 58, 110, 40)
        self.generator_buttons = {"new_seed": new_seed, "generate": generate, "close": close}

        for name, rect, label in (
            ("new_seed", new_seed, "🎲 New Seed"),
            ("generate", generate, "Generate New Room"),
            ("close", close, "Close"),
        ):
            primary = name == "generate"
            fill = self.theme_rgb["accent"] if primary else self.theme_rgb["panel_alt"]
            foreground = self.theme_rgb["background"] if primary else self.theme_rgb["text"]
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            image = self.font_small.render(label, True, foreground)
            self.screen.blit(image, image.get_rect(center=rect.center))

        dynamic_draw_text(
            self.screen,
            "Generation creates a new room. Your current room is never overwritten.",
            box.x + 452,
            box.bottom - 28,
            self.font_small,
            self.theme_rgb["muted_text"],
        )

    def draw_generator_preview(self, rect: pygame.Rect) -> None:
        if not self.generator_preview:
            return

        width = int(self.generator_preview.get("generator", {}).get("width", 24))
        height = int(self.generator_preview.get("generator", {}).get("height", 20))
        tile = min((rect.width - 20) // width, (rect.height - 20) // height)
        tile = max(4, tile)
        origin_x = rect.centerx - width * tile // 2
        origin_y = rect.centery - height * tile // 2

        layers = self.generator_preview.get("layers", {})
        for y in range(height):
            for x in range(width):
                pygame.draw.rect(
                    self.screen,
                    self.theme_rgb["grid"],
                    (origin_x + x * tile, origin_y + y * tile, tile, tile),
                    1,
                )

        preview_order = ("map", "scene_objects", "decorations", "actors", "weapons")
        for layer in preview_order:
            for item in layers.get(layer, []):
                x, y = int(item.get("x", 0)), int(item.get("y", 0))
                if not (0 <= x < width and 0 <= y < height):
                    continue
                color = tuple(item.get("color", [180, 180, 180]))
                inset = 1 if tile >= 8 else 0
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        origin_x + x * tile + inset,
                        origin_y + y * tile + inset,
                        max(1, tile - inset * 2),
                        max(1, tile - inset * 2),
                    ),
                    border_radius=1,
                )

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend([
                "## Generate a Map",
                "55. Open Maps from the top bar.",
                "56. Choose Forest, Village, Dungeon, Cave, Maze, or Arena.",
                "57. Press New Seed to create a different repeatable layout.",
                "58. Press Generate New Room. The current room is never overwritten.",
                "59. Edit the generated room normally after it opens.",
            ])
        else:
            content.extend([
                "## Seeded Map Generator",
                "The same style and seed always create the same room layout.",
                "Generated rooms include a player, enemies, treasure, a weapon, decorations, atmosphere, and an exit.",
            ])
        return content
