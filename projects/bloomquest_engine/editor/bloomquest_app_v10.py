# bloomquest_app_v10.py
# run with: imported by bloomquest_v10.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v10.py
# description: Adds editable enemy behavior, movement, damage, rewards, death effects, and respawn settings.
# version: 0.10.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, enemies, ai, properties, combat, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, gamepad optional
# notes: Behavior values are idle, patrol, wander, or chase. Respawn uses 0 or 1.
# uuid: bc-bloomquest-app-0010

from __future__ import annotations

import json
from copy import deepcopy

import pygame

from editor.bloomquest_app import (
    CANVAS_HEIGHT,
    CANVAS_LEFT,
    CANVAS_TOP,
    CANVAS_WIDTH,
    TILE_SIZE,
    TextField,
    safe_int,
)
from editor.bloomquest_app_v09 import BloomQuestAppV09
from engine.world_play_v10 import WorldPlayV10


class BloomQuestAppV10(BloomQuestAppV09):
    """BloomQuest v0.10 with editable enemy AI settings."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.10")
        self.status_message = "v0.10 ready. Select a Slime or Bat to configure enemy behavior."

    def is_enemy(self, target=None) -> bool:
        item = target or self.selected_instance
        if not item:
            return False
        return item.get("part_id") not in ("player", "villager") and (
            "health" in item or item.get("layer") == "actors"
        )

    def build_fields(self) -> None:
        """Build normal fields plus enemy-specific AI controls."""
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
        ]

        if self.is_enemy(target):
            self.fields.extend(
                [
                    TextField("behavior", "Behavior", target.get("behavior", "idle")),
                    TextField("move_delay", "Move Delay ms", target.get("move_delay", 400), numeric=True),
                    TextField("detection_range", "Detection Range", target.get("detection_range", 6), numeric=True),
                    TextField("hit_cooldown", "Hit Cooldown ms", target.get("hit_cooldown", 900), numeric=True),
                    TextField("score_reward", "Score Reward", target.get("score_reward", 1), numeric=True),
                    TextField("patrol_axis", "Patrol Axis", target.get("patrol_axis", "horizontal")),
                    TextField("death_effect", "Death Effect", target.get("death_effect", "sparkle")),
                    TextField("respawn", "Respawn 0/1", int(bool(target.get("respawn", False))), numeric=True),
                    TextField("respawn_delay", "Respawn Delay ms", target.get("respawn_delay", 3000), numeric=True),
                ]
            )

        self.fields.extend(
            [
                TextField("target_room", "Target Room", action.get("target_room", "")),
                TextField("target_x", "Target X", action.get("target_x", 0), numeric=True),
                TextField("target_y", "Target Y", action.get("target_y", 0), numeric=True),
                TextField("seconds", "Timer Seconds", action.get("seconds", 0), numeric=True),
            ]
        )
        self.field_by_key = {field.key: field for field in self.fields}

    def apply_properties(self) -> None:
        """Apply common properties and normalized enemy settings."""
        if not self.selected_instance:
            return

        target = self.selected_instance
        target["emoji"] = self.field_by_key["emoji"].value.strip()
        target["name"] = self.field_by_key["name"].value.strip() or "Part"
        target["description"] = self.field_by_key["description"].value.strip()
        target["health"] = safe_int(self.field_by_key["health"].value, target.get("health", 0))
        target["damage"] = safe_int(self.field_by_key["damage"].value, target.get("damage", 0))

        action = target.setdefault("action", {})
        for key in ("text", "counter", "target_room"):
            action[key] = self.field_by_key[key].value.strip()
        for key in ("amount", "target_x", "target_y", "seconds"):
            action[key] = safe_int(self.field_by_key[key].value, action.get(key, 0))

        if self.is_enemy(target):
            behavior = self.field_by_key["behavior"].value.strip().lower()
            if behavior not in ("idle", "patrol", "wander", "chase"):
                behavior = "idle"

            patrol_axis = self.field_by_key["patrol_axis"].value.strip().lower()
            if patrol_axis not in ("horizontal", "vertical"):
                patrol_axis = "horizontal"

            death_effect = self.field_by_key["death_effect"].value.strip().lower()
            if death_effect not in ("sparkle", "explosion"):
                death_effect = "sparkle"

            target["behavior"] = behavior
            target["move_delay"] = max(80, safe_int(self.field_by_key["move_delay"].value, 400))
            target["detection_range"] = max(1, safe_int(self.field_by_key["detection_range"].value, 6))
            target["hit_cooldown"] = max(250, safe_int(self.field_by_key["hit_cooldown"].value, 900))
            target["score_reward"] = max(0, safe_int(self.field_by_key["score_reward"].value, 1))
            target["patrol_axis"] = patrol_axis
            target["patrol_direction"] = int(target.get("patrol_direction", 1)) or 1
            target["death_effect"] = death_effect
            target["respawn"] = bool(safe_int(self.field_by_key["respawn"].value, 0))
            target["respawn_delay"] = max(500, safe_int(self.field_by_key["respawn_delay"].value, 3000))
            target["max_health"] = max(1, target["health"])

        self.status_message = f"Updated {target['name']}"

    def save_selected_as_new_part(self) -> None:
        """Save custom enemy AI values into the active project library."""
        selected = self.selected_instance
        super().save_selected_as_new_part()
        if not selected or not self.parts:
            return

        new_part = self.parts[-1]
        for key in (
            "behavior",
            "move_delay",
            "detection_range",
            "hit_cooldown",
            "score_reward",
            "patrol_axis",
            "patrol_direction",
            "death_effect",
            "respawn",
            "respawn_delay",
            "max_health",
        ):
            if key in selected:
                new_part[key] = deepcopy(selected[key])

        parts_path = self.project_manager.parts_file(self.project_id)
        with parts_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("parts"):
            payload["parts"][-1] = deepcopy(new_part)
        with parts_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def place_or_select(self, gx: int, gy: int) -> None:
        """Place normally, then copy AI defaults from reusable enemy parts."""
        previous_count = len(self.room.get("layers", {}).get(self.active_layer, []))
        super().place_or_select(gx, gy)
        current_count = len(self.room.get("layers", {}).get(self.active_layer, []))

        if not self.selected_instance or current_count <= previous_count:
            return

        selected_part = self.selected_part
        if selected_part.get("layer") != "actors" or selected_part.get("id") in ("player", "villager"):
            return

        defaults = {
            "behavior": "idle",
            "move_delay": 400,
            "detection_range": 6,
            "hit_cooldown": 900,
            "score_reward": 1,
            "patrol_axis": "horizontal",
            "patrol_direction": 1,
            "death_effect": "sparkle",
            "respawn": False,
            "respawn_delay": 3000,
        }
        for key, fallback in defaults.items():
            self.selected_instance[key] = deepcopy(selected_part.get(key, fallback))
        self.selected_instance["max_health"] = max(1, int(self.selected_instance.get("health", 1)))
        self.build_fields()

    def enter_play_mode(self) -> None:
        """Start the v0.10 runtime while keeping project isolation."""
        self.save_current_room()
        has_player = any(
            item.get("part_id") == "player"
            for item in self.room.get("layers", {}).get("actors", [])
        )
        if not has_player:
            self.status_message = "Place a Player in this room first."
            return

        self.world_play = WorldPlayV10(
            self.room_manager,
            self.current_room_id,
            TILE_SIZE,
            pygame.Rect(CANVAS_LEFT, CANVAS_TOP, CANVAS_WIDTH, CANVAS_HEIGHT),
        )
        self.mode = "play"
        self.overlay = None
        pygame.display.set_caption("BloomQuest Engine v0.10 — PLAY MODE")

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        pygame.draw.rect(self.screen, (35, 39, 47), (0, 0, 205, TOP_BAR_HEIGHT))

        from editor.bloomquest_app import MUTED_TEXT, draw_text

        draw_text(self.screen, "BloomQuest v0.10", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

    def draw_play_mode(self) -> None:
        super().draw_play_mode()

        from editor.bloomquest_app import MUTED_TEXT, TOP_BAR_HEIGHT, draw_text

        draw_text(self.screen, "Enemy AI:", 18, TOP_BAR_HEIGHT + 454, self.font_small)
        draw_text(self.screen, "Idle / Patrol / Wander", 18, TOP_BAR_HEIGHT + 478, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Chase uses detection range", 18, TOP_BAR_HEIGHT + 502, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "Touch causes damage", 18, TOP_BAR_HEIGHT + 526, self.font_small, MUTED_TEXT)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Configure an Enemy",
                    "35. Place a Slime or Bat and select it.",
                    "36. Set Behavior to idle, patrol, wander, or chase.",
                    "37. Set movement delay, detection range, damage, and hit cooldown.",
                    "38. Set score reward and death effect to sparkle or explosion.",
                    "39. Set Respawn to 1 to bring the enemy back after its delay.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Patrol",
                    "An enemy walks along one axis and reverses when blocked.",
                    "## Wander",
                    "An enemy chooses random nearby movement directions.",
                    "## Chase",
                    "An enemy follows the player when inside its detection range.",
                    "## Hit Cooldown",
                    "Temporary protection preventing contact damage every frame.",
                    "## Respawn",
                    "A defeated enemy returns after a chosen delay.",
                ]
            )
        else:
            content.extend(
                [
                    "## Enemy Behavior",
                    "Enemies support idle, patrol, wander, and chase behavior.",
                    "Contact causes damage with a safety cooldown.",
                    "Sword defeats can create sparkle or explosion effects and award score.",
                    "Respawning enemies return at their original placement position.",
                ]
            )

        return content
