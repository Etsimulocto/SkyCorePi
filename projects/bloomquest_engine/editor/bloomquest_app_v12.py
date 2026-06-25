# bloomquest_app_v12.py
# run with: imported by bloomquest_v12.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v12.py
# description: Adds editable damage, speed, range, cooldown, radius, fuse, and projectile symbols for weapons.
# version: 0.12.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, properties, bow, wand, bombs, sword, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Weapon settings are stored on each placed weapon and used immediately in Play Mode.
# uuid: bc-bloomquest-app-0012

from __future__ import annotations

import pygame

from editor.bloomquest_app import MUTED_TEXT, TOP_BAR_HEIGHT, TextField, draw_text, safe_int
from editor.bloomquest_app_v112 import BloomQuestAppV112


class BloomQuestAppV12(BloomQuestAppV112):
    """BloomQuest v0.12 with per-instance weapon tuning."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.12 — Weapon Properties")
        self.status_message = "Select a placed weapon to edit its combat properties."

    def is_weapon(self, target=None) -> bool:
        item = target or self.selected_instance
        return bool(item and item.get("weapon"))

    def build_fields(self) -> None:
        """Build inherited fields and append controls for the selected weapon type."""
        super().build_fields()
        if not self.is_weapon() or not self.selected_instance:
            return

        target = self.selected_instance
        settings = target.setdefault("weapon", {})
        weapon_type = str(settings.get("type", "orbit")).lower()

        weapon_fields = [
            TextField("weapon_damage", "Weapon Damage", target.get("damage", 1), numeric=True),
            TextField("weapon_cooldown", "Cooldown ms", settings.get("cooldown_ms", 0), numeric=True),
        ]

        if weapon_type == "orbit":
            weapon_fields.extend(
                [
                    TextField("weapon_radius", "Orbit Radius Tiles", settings.get("radius", 1), numeric=True),
                    TextField("weapon_speed", "Orbit Step ms", settings.get("speed_ms", 120), numeric=True),
                ]
            )
        elif weapon_type == "projectile":
            weapon_fields.extend(
                [
                    TextField("projectile_emoji", "Projectile Symbol", settings.get("projectile_emoji", "•")),
                    TextField("weapon_speed", "Projectile Step ms", settings.get("speed_ms", 90), numeric=True),
                    TextField("weapon_range", "Projectile Range", settings.get("range", 8), numeric=True),
                ]
            )
        elif weapon_type == "bomb":
            weapon_fields.extend(
                [
                    TextField("weapon_fuse", "Fuse ms", settings.get("fuse_ms", 1200), numeric=True),
                    TextField("weapon_radius", "Blast Radius Tiles", settings.get("radius", 1), numeric=True),
                ]
            )

        insert_at = next(
            (index for index, field in enumerate(self.fields) if field.key == "target_room"),
            len(self.fields),
        )
        self.fields[insert_at:insert_at] = weapon_fields
        self.field_by_key = {field.key: field for field in self.fields}

    def apply_properties(self) -> None:
        """Apply normal properties, then normalize weapon-specific values."""
        if not self.selected_instance:
            return

        super().apply_properties()

        target = self.selected_instance
        if not self.is_weapon(target):
            return

        settings = target.setdefault("weapon", {})
        weapon_type = str(settings.get("type", "orbit")).lower()

        damage_field = self.field_by_key.get("weapon_damage")
        cooldown_field = self.field_by_key.get("weapon_cooldown")
        if damage_field:
            target["damage"] = max(1, safe_int(damage_field.value, target.get("damage", 1)))
        if cooldown_field:
            settings["cooldown_ms"] = max(0, safe_int(cooldown_field.value, settings.get("cooldown_ms", 0)))

        if weapon_type == "orbit":
            radius_field = self.field_by_key.get("weapon_radius")
            speed_field = self.field_by_key.get("weapon_speed")
            if radius_field:
                settings["radius"] = max(1, safe_int(radius_field.value, settings.get("radius", 1)))
            if speed_field:
                settings["speed_ms"] = max(25, safe_int(speed_field.value, settings.get("speed_ms", 120)))

        elif weapon_type == "projectile":
            emoji_field = self.field_by_key.get("projectile_emoji")
            speed_field = self.field_by_key.get("weapon_speed")
            range_field = self.field_by_key.get("weapon_range")
            if emoji_field:
                settings["projectile_emoji"] = emoji_field.value.strip() or "•"
            if speed_field:
                settings["speed_ms"] = max(25, safe_int(speed_field.value, settings.get("speed_ms", 90)))
            if range_field:
                settings["range"] = max(1, safe_int(range_field.value, settings.get("range", 8)))

        elif weapon_type == "bomb":
            fuse_field = self.field_by_key.get("weapon_fuse")
            radius_field = self.field_by_key.get("weapon_radius")
            if fuse_field:
                settings["fuse_ms"] = max(100, safe_int(fuse_field.value, settings.get("fuse_ms", 1200)))
            if radius_field:
                settings["radius"] = max(1, safe_int(radius_field.value, settings.get("radius", 1)))

        self.status_message = f"Updated {target.get('name', 'weapon')} combat settings"

    def place_or_select(self, gx: int, gy: int) -> None:
        """Ensure freshly placed repaired weapons immediately show their settings."""
        super().place_or_select(gx, gy)
        if self.is_weapon():
            self.build_fields()

    def draw_top_bar(self) -> None:
        super().draw_top_bar()
        pygame.draw.rect(self.screen, (35, 39, 47), (0, 0, 205, TOP_BAR_HEIGHT))
        draw_text(self.screen, "BloomQuest v0.12", 10, 4, self.font_large)
        draw_text(self.screen, self.project_id, 12, 31, self.font_small, MUTED_TEXT)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)
        if page == "directions":
            content.extend(
                [
                    "## Tune a Weapon",
                    "47. Place a weapon and select it on the map.",
                    "48. Scroll through Properties to the weapon settings.",
                    "49. Change damage, speed, range, cooldown, radius, fuse, or projectile symbol.",
                    "50. Press Apply Changes, then enter Play Mode.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Orbit Step",
                    "Milliseconds between each sword movement step. Lower values move faster.",
                    "## Projectile Step",
                    "Milliseconds between projectile tile movements. Lower values move faster.",
                    "## Blast Radius",
                    "How many tiles from a bomb can receive damage.",
                ]
            )
        else:
            content.extend(
                [
                    "## Weapon Properties",
                    "Sword supports damage, cooldown, orbit radius, and orbit speed.",
                    "Bow and Wand support damage, cooldown, symbol, speed, and range.",
                    "Bombs support damage, cooldown, fuse time, and blast radius.",
                ]
            )
        return content
