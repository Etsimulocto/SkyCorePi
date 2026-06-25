# bloomquest_app_v09.py
# run with: imported by bloomquest_v09.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v09.py
# description: Adds external user projects, project switching, duplication, and safe custom-part storage.
# version: 0.9.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, projects, workspace, migration, safety, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: User projects live in ~/BloomQuestProjects, outside the Git repository.
# uuid: bc-bloomquest-app-0009

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    MUTED_TEXT,
    PANEL,
    PANEL_ALT,
    TEXT,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v081 import BloomQuestAppV081
from editor.bloomquest_app_v08 import LAYER_LABELS_V08
from engine.project_manager import ProjectManager
from engine.room_manager import RoomManager


class BloomQuestAppV09(BloomQuestAppV081):
    """BloomQuest v0.9 with user projects stored outside the engine repo."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.9")

        self.project_manager = ProjectManager(self.room_manager.rooms_dir.parents[1])
        self.project = self.project_manager.ensure_first_project()
        self.project_id = self.project["project_id"]

        self.project_button = pygame.Rect(784, 10, 92, 34)
        self.rooms_button = pygame.Rect(882, 10, 78, 34)
        self.help_button = pygame.Rect(966, 10, 72, 34)
        self.play_button = pygame.Rect(1044, 10, 82, 34)

        self.open_project(self.project_id, save_current=False)
        self.overlay = "projects"
        self.status_message = f"Project data is protected in {self.project_manager.projects_root}"

    def load_project_parts(self) -> None:
        """Load the active project's private part library."""
        parts_path = self.project_manager.parts_file(self.project_id)
        with parts_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.parts = payload.get("parts", [])
        if not self.parts:
            raise ValueError(f"Project has no parts: {parts_path}")

    def open_project(self, project_id: str, save_current: bool = True) -> None:
        """Switch the complete editor workspace to another project."""
        if save_current and hasattr(self, "project_id"):
            self.save_current_room()
            self.project_manager.save_project(self.project)

        self.project = self.project_manager.load_project(project_id)
        self.project_id = project_id
        self.load_project_parts()

        rooms_dir = self.project_manager.rooms_dir(project_id)
        self.room_manager = RoomManager(rooms_dir, 128, 128, 32)
        room_ids = self.room_manager.list_room_ids()
        start_room = self.project.get("start_room", "room_001")
        self.current_room_id = start_room if start_room in room_ids else (room_ids[0] if room_ids else "room_001")
        self.room = self.room_manager.load(self.current_room_id)
        self.room.setdefault("layers", {}).setdefault("weapons", [])

        self.active_layer = "map"
        self.selected_part_index = next(
            (index for index, part in enumerate(self.parts) if part.get("layer") == "map"),
            0,
        )
        self.camera_x = 0
        self.camera_y = 0
        self.palette_scroll = 0
        self.clear_selection()
        self.overlay = None
        self.status_message = f"Opened project: {self.project.get('name', project_id)}"
        pygame.display.set_caption(f"BloomQuest v0.9 — {self.project.get('name', project_id)}")

    def save_current_room(self) -> None:
        """Save room and project metadata into the external workspace."""
        self.room_manager.save(self.room)
        self.project["start_room"] = self.project.get("start_room", self.current_room_id)
        self.project_manager.save_project(self.project)
        self.status_message = f"Saved {self.project_id}/{self.current_room_id}"

    def save_selected_as_new_part(self) -> None:
        """Save a custom part only into the active project library."""
        if not self.selected_instance:
            self.status_message = "Select a placed object first."
            return

        source = self.selected_instance
        name = str(source.get("name", "Custom Part"))
        base_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "custom_part"
        existing_ids = {str(part.get("id", "")) for part in self.parts}
        part_id = base_id
        suffix = 2
        while part_id in existing_ids:
            part_id = f"{base_id}_{suffix}"
            suffix += 1

        new_part: dict[str, Any] = {
            "id": part_id,
            "emoji": source.get("emoji", ""),
            "name": name,
            "description": source.get("description", ""),
            "layer": source.get("layer", self.active_layer),
            "color": deepcopy(source.get("color", [180, 180, 180])),
            "solid": bool(source.get("solid", False)),
            "custom": True,
        }
        for key in ("action", "health", "damage", "weapon"):
            if key in source:
                new_part[key] = deepcopy(source[key])

        parts_path = self.project_manager.parts_file(self.project_id)
        with parts_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload.setdefault("parts", []).append(new_part)
        with parts_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        self.parts.append(new_part)
        self.active_layer = new_part["layer"]
        self.selected_part_index = len(self.parts) - 1
        self.status_message = f"Saved {new_part['name']} inside project {self.project_id}"

    def handle_click(self, event: pygame.event.Event) -> None:
        """Handle the new Project toolbar before inherited controls."""
        if self.mode == "edit" and not self.overlay and event.pos[1] < TOP_BAR_HEIGHT:
            x, y = event.pos

            if self.project_button.collidepoint(x, y):
                self.overlay = "projects"
                self.overlay_scroll = 0
                return
            if self.rooms_button.collidepoint(x, y):
                self.overlay = "rooms"
                self.overlay_scroll = 0
                return
            if self.help_button.collidepoint(x, y):
                self.overlay = "help"
                self.overlay_scroll = 0
                return
            if self.play_button.collidepoint(x, y):
                self.enter_play_mode()
                return

            button_x = 210
            for layer in ("map", "scene_objects", "actors", "weapons", "weapons_effects"):
                rect = pygame.Rect(button_x, 10, 108, 34)
                if rect.collidepoint(x, y):
                    self.set_layer(layer)
                    return
                button_x += 114
            return

        super().handle_click(event)

    def handle_overlay_click(self, x: int, y: int) -> None:
        """Handle project cards and delegate other overlays."""
        if self.overlay != "projects":
            super().handle_overlay_click(x, y)
            return

        for name, rect in self.overlay_buttons:
            if not rect.collidepoint(x, y):
                continue

            if name == "close":
                self.overlay = None
            elif name == "new_project":
                project = self.project_manager.create_project()
                self.open_project(project["project_id"])
            elif name == "duplicate_project":
                project = self.project_manager.duplicate_project(self.project_id)
                self.open_project(project["project_id"])
            elif name.startswith("project:"):
                self.open_project(name.split(":", 1)[1])
            return

    def draw_top_bar(self) -> None:
        """Draw compact project, layer, room, help, and play controls."""
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.9", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

        if self.mode != "edit":
            return

        button_x = 210
        short_labels = {
            "map": "Map",
            "scene_objects": "Objects",
            "actors": "Actors",
            "weapons": "Weapons",
            "weapons_effects": "Effects",
        }
        for layer in ("map", "scene_objects", "actors", "weapons", "weapons_effects"):
            rect = pygame.Rect(button_x, 10, 108, 34)
            active = layer == self.active_layer
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(short_labels[layer], True, BACKGROUND if active else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))
            button_x += 114

        for rect, label in (
            (self.project_button, "Projects"),
            (self.rooms_button, "Rooms"),
            (self.help_button, "Help"),
            (self.play_button, "▶ Play"),
        ):
            is_play = label == "▶ Play"
            pygame.draw.rect(self.screen, ACCENT if is_play else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND if is_play else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def draw_overlay(self) -> None:
        if self.overlay != "projects":
            super().draw_overlay()
            return

        shade = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 185))
        self.screen.blit(shade, (0, 0))
        box = pygame.Rect(150, 76, self.screen.get_width() - 300, self.screen.get_height() - 152)
        pygame.draw.rect(self.screen, PANEL, box, border_radius=10)
        pygame.draw.rect(self.screen, ACCENT, box, 2, border_radius=10)
        self.overlay_buttons = []

        draw_text(self.screen, "BloomQuest Projects", box.x + 24, box.y + 18, self.font_title)
        draw_text(
            self.screen,
            str(self.project_manager.projects_root),
            box.x + 26,
            box.y + 58,
            self.font_small,
            MUTED_TEXT,
        )

        close_rect = pygame.Rect(box.right - 92, box.y + 16, 70, 34)
        pygame.draw.rect(self.screen, PANEL_ALT, close_rect, border_radius=5)
        close_image = self.font_small.render("Close", True, TEXT)
        self.screen.blit(close_image, close_image.get_rect(center=close_rect.center))
        self.overlay_buttons.append(("close", close_rect))

        new_rect = pygame.Rect(box.x + 24, box.y + 94, 150, 38)
        duplicate_rect = pygame.Rect(box.x + 184, box.y + 94, 190, 38)
        for name, rect, label in (
            ("new_project", new_rect, "+ New Project"),
            ("duplicate_project", duplicate_rect, "Duplicate Current"),
        ):
            pygame.draw.rect(self.screen, ACCENT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND)
            self.screen.blit(image, image.get_rect(center=rect.center))
            self.overlay_buttons.append((name, rect))

        y = box.y + 154 - self.overlay_scroll
        for project in self.project_manager.list_projects():
            project_id = project.get("project_id", "Unknown")
            rect = pygame.Rect(box.x + 24, y, box.width - 48, 64)
            active = project_id == self.project_id
            pygame.draw.rect(self.screen, (72, 83, 78) if active else PANEL_ALT, rect, border_radius=7)
            draw_text(self.screen, project.get("name", project_id), rect.x + 14, rect.y + 10, self.font_medium)
            draw_text(self.screen, project_id, rect.x + 14, rect.y + 38, self.font_small, MUTED_TEXT)
            draw_text(self.screen, project.get("start_room", "room_001"), rect.right - 120, rect.y + 22, self.font_small, MUTED_TEXT)
            self.overlay_buttons.append((f"project:{project_id}", rect))
            y += 74

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend(
                [
                    "## Projects",
                    "32. Open Projects to create, duplicate, or switch games.",
                    "33. Each project owns its rooms, parts, saves, and exports.",
                    "34. Projects live outside Git in your BloomQuestProjects folder.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Project",
                    "A complete game workspace containing private rooms, parts, saves, and exports.",
                    "## Workspace",
                    "The external folder protecting user-created data from engine updates.",
                ]
            )
        else:
            content.extend(
                [
                    "## Project Safety",
                    "User games are stored in ~/BloomQuestProjects instead of the Git repository.",
                    "The first launch migrates existing rooms and custom parts into My_Adventure.",
                    "Git pulls can now update the engine without overwriting game content.",
                ]
            )
        return content
