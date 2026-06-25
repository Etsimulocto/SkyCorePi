# bloomquest_app_v05.py
# run with: imported by bloomquest_v05.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v05.py
# description: Extends BloomQuest v0.4 with editable emojis and Save as New Part support.
# version: 0.5.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, editor, custom-parts, emoji, json, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Custom parts are written to data/parts/parts_library.json and appear immediately in the palette.
# uuid: bc-bloomquest-app-0005

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    CANVAS_RIGHT,
    FIELD,
    GRID_LINE,
    MUTED_TEXT,
    PANEL,
    PANEL_ALT,
    PARTS_FILE,
    PROPERTIES_WIDTH,
    SELECTION,
    TEXT,
    TOP_BAR_HEIGHT,
    BloomQuestApp,
    TextField,
    draw_text,
    safe_int,
)


class BloomQuestAppV05(BloomQuestApp):
    """BloomQuest editor with permanent user-created parts."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.5")
        self.save_part_button = pygame.Rect(0, 0, 0, 0)
        self.status_message = "v0.5 ready. Customize a placed object and save it as a new part."

    def build_fields(self) -> None:
        if not self.selected_instance:
            return

        target = self.selected_instance
        action = target.get("action", {})
        self.fields = [
            TextField("emoji", "Emoji / Symbol", target.get("emoji", "")),
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

    def apply_properties(self) -> None:
        if not self.selected_instance:
            return

        target = self.selected_instance
        target["emoji"] = self.field_by_key["emoji"].value.strip()
        target["name"] = self.field_by_key["name"].value.strip() or "Custom Part"
        target["description"] = self.field_by_key["description"].value.strip()
        target["health"] = safe_int(self.field_by_key["health"].value, target.get("health", 0))
        target["damage"] = safe_int(self.field_by_key["damage"].value, target.get("damage", 0))

        action = target.setdefault("action", {})
        for key in ("text", "counter", "target_room"):
            action[key] = self.field_by_key[key].value.strip()
        for key in ("amount", "target_x", "target_y", "seconds"):
            action[key] = safe_int(self.field_by_key[key].value, action.get(key, 0))

        self.status_message = f"Updated {target['name']}"

    def handle_click(self, event: pygame.event.Event) -> None:
        if (
            self.mode == "edit"
            and not self.overlay
            and self.selected_instance
            and self.save_part_button.collidepoint(event.pos)
        ):
            self.apply_properties()
            self.save_selected_as_new_part()
            return

        super().handle_click(event)

    def make_part_id(self, name: str) -> str:
        base_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "custom_part"
        existing_ids = {str(part.get("id", "")) for part in self.parts}

        if base_id not in existing_ids:
            return base_id

        suffix = 2
        while f"{base_id}_{suffix}" in existing_ids:
            suffix += 1
        return f"{base_id}_{suffix}"

    def save_selected_as_new_part(self) -> None:
        if not self.selected_instance:
            self.status_message = "Select a placed object first."
            return

        source = self.selected_instance
        part_id = self.make_part_id(str(source.get("name", "Custom Part")))

        new_part: dict[str, Any] = {
            "id": part_id,
            "emoji": source.get("emoji", ""),
            "name": source.get("name", "Custom Part"),
            "description": source.get("description", ""),
            "layer": source.get("layer", self.active_layer),
            "color": deepcopy(source.get("color", [180, 180, 180])),
            "solid": bool(source.get("solid", False)),
            "custom": True,
        }

        for optional_key in ("action", "health", "damage"):
            if optional_key in source:
                new_part[optional_key] = deepcopy(source[optional_key])

        try:
            with PARTS_FILE.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError):
            payload = {"format": "bloomquest/parts-v0.1", "tile_size": 32, "parts": []}

        payload.setdefault("format", "bloomquest/parts-v0.1")
        payload.setdefault("tile_size", 32)
        payload.setdefault("parts", [])
        payload["parts"].append(new_part)

        with PARTS_FILE.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        self.parts.append(new_part)
        self.active_layer = new_part["layer"]
        self.selected_part_index = len(self.parts) - 1
        self.palette_scroll = max(0, len(self.visible_parts()) * 48 - 500)
        self.status_message = f"Saved new reusable part: {new_part['name']} ({part_id})"

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        title_rect = pygame.Rect(0, 0, 275, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, PANEL, title_rect)
        draw_text(self.screen, f"BloomQuest v0.5 — {self.current_room_id}", 14, 13, self.font_large)

    def draw_properties(self) -> None:
        pygame.draw.rect(
            self.screen,
            PANEL,
            (CANVAS_RIGHT, TOP_BAR_HEIGHT, PROPERTIES_WIDTH, self.screen.get_height() - TOP_BAR_HEIGHT),
        )
        draw_text(self.screen, "Properties", CANVAS_RIGHT + 16, TOP_BAR_HEIGHT + 14, self.font_medium)

        if not self.selected_instance:
            draw_text(
                self.screen,
                "Place a part, then click it again",
                CANVAS_RIGHT + 16,
                TOP_BAR_HEIGHT + 64,
                self.font_small,
                MUTED_TEXT,
            )
            draw_text(
                self.screen,
                "to edit it or create a reusable part.",
                CANVAS_RIGHT + 16,
                TOP_BAR_HEIGHT + 88,
                self.font_small,
                MUTED_TEXT,
            )
            self.save_part_button = pygame.Rect(0, 0, 0, 0)
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
        action_label = self.font_small.render(target.get("action", {}).get("type", "none"), True, TEXT)
        self.screen.blit(action_label, action_label.get_rect(center=self.action_button.center))
        y += 48

        for field in self.fields:
            draw_text(self.screen, field.label, CANVAS_RIGHT + 16, y, self.font_small, MUTED_TEXT)
            y += 21
            height = 54 if field.multiline else 34
            field.rect = pygame.Rect(CANVAS_RIGHT + 16, y, PROPERTIES_WIDTH - 32, height)
            pygame.draw.rect(self.screen, (52, 61, 72) if field.active else FIELD, field.rect, border_radius=5)
            pygame.draw.rect(
                self.screen,
                ACCENT if field.active else GRID_LINE,
                field.rect,
                2,
                border_radius=5,
            )
            draw_text(self.screen, field.value[-70:], field.rect.x + 7, field.rect.y + 7, self.font_small)
            y += height + 11

        self.apply_button = pygame.Rect(CANVAS_RIGHT + 16, y + 4, PROPERTIES_WIDTH - 32, 40)
        pygame.draw.rect(self.screen, ACCENT, self.apply_button, border_radius=6)
        apply_label = self.font_small.render("Apply Changes", True, BACKGROUND)
        self.screen.blit(apply_label, apply_label.get_rect(center=self.apply_button.center))

        y += 52
        self.save_part_button = pygame.Rect(CANVAS_RIGHT + 16, y + 4, PROPERTIES_WIDTH - 32, 40)
        pygame.draw.rect(self.screen, SELECTION, self.save_part_button, border_radius=6)
        save_label = self.font_small.render("Save as New Part", True, BACKGROUND)
        self.screen.blit(save_label, save_label.get_rect(center=self.save_part_button.center))

        draw_text(
            self.screen,
            "Adds a permanent copy to the palette.",
            CANVAS_RIGHT + 20,
            y + 50,
            self.font_small,
            MUTED_TEXT,
        )

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Create a Custom Part",
                    "13. Place the closest premade part.",
                    "14. Edit its Emoji, Name, Description, action, and values.",
                    "15. Press Apply Changes.",
                    "16. Scroll down and press Save as New Part.",
                    "17. The reusable part appears in its layer palette immediately.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Custom Part",
                    "A reusable part created from a customized placed object.",
                    "## Part Library",
                    "The permanent JSON list used to build the left palette.",
                ]
            )
        else:
            content.extend(
                [
                    "## Custom Parts",
                    "Select a placed object and edit its Emoji, Name, Description, action, and values.",
                    "Press Apply Changes, then Save as New Part.",
                    "The new reusable part is stored in data/parts/parts_library.json.",
                ]
            )

        return content
