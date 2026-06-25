# world_play_v10.py
# run with: imported by editor/bloomquest_app_v10.py
# path: projects/bloomquest_engine/engine/world_play_v10.py
# description: Enemy AI runtime with idle, patrol, wander, chase, contact damage, knockback, death effects, rewards, and respawn.
# version: 0.10.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, enemies, ai, chase, patrol, combat, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Enemy settings are stored directly on each placed enemy instance.
# uuid: bc-bloomquest-worldplay-0010

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import pygame

from engine.world_play_v08 import LAYER_ORDER_V08, WorldPlayV08


class WorldPlayV10(WorldPlayV08):
    """Play runtime with simple grid-based enemy behavior."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.enemy_last_move: dict[str, int] = {}
        self.enemy_spawn_data: dict[str, dict[str, Any]] = {}
        self.enemy_respawn_due: list[dict[str, Any]] = []
        self.player_invulnerable_until = 0
        self.effects: list[dict[str, Any]] = []
        self.capture_enemy_spawns()

    def capture_enemy_spawns(self) -> None:
        for enemy in self.enemy_items():
            key = self.enemy_key(enemy)
            self.enemy_spawn_data[key] = deepcopy(enemy)

    def enemy_items(self) -> list[dict[str, Any]]:
        return [
            item
            for item in self.room.get("layers", {}).get("actors", [])
            if item.get("part_id") not in ("player", "villager") and "health" in item
        ]

    @staticmethod
    def enemy_key(enemy: dict[str, Any]) -> str:
        return str(enemy.get("instance_id") or f"{enemy.get('part_id', 'enemy')}:{enemy.get('x', 0)}:{enemy.get('y', 0)}")

    def update(self) -> None:
        super().update()
        now = pygame.time.get_ticks()
        self.update_enemies(now)
        self.update_respawns(now)
        self.effects = [effect for effect in self.effects if effect.get("until", 0) > now]

    def update_enemies(self, now: int) -> None:
        for enemy in list(self.enemy_items()):
            key = self.enemy_key(enemy)
            delay = max(80, int(enemy.get("move_delay", 400)))
            if now - self.enemy_last_move.get(key, 0) < delay:
                continue

            self.enemy_last_move[key] = now
            behavior = str(enemy.get("behavior", "idle")).lower()
            dx, dy = 0, 0

            if behavior == "patrol":
                dx, dy = self.patrol_direction(enemy)
            elif behavior == "wander":
                dx, dy = random.choice(((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)))
            elif behavior == "chase":
                dx, dy = self.chase_direction(enemy)

            if dx or dy:
                self.try_move_enemy(enemy, dx, dy)

            if self.enemy_touches_player(enemy):
                self.damage_player_from_enemy(enemy, now)

    def patrol_direction(self, enemy: dict[str, Any]) -> tuple[int, int]:
        direction = int(enemy.get("patrol_direction", 1))
        axis = str(enemy.get("patrol_axis", "horizontal")).lower()
        if axis == "vertical":
            return 0, direction
        return direction, 0

    def chase_direction(self, enemy: dict[str, Any]) -> tuple[int, int]:
        ex, ey = int(enemy.get("x", 0)), int(enemy.get("y", 0))
        distance = abs(self.player_x - ex) + abs(self.player_y - ey)
        detection = max(1, int(enemy.get("detection_range", 6)))
        if distance > detection:
            return 0, 0

        horizontal = self.player_x - ex
        vertical = self.player_y - ey
        if abs(horizontal) >= abs(vertical) and horizontal:
            return 1 if horizontal > 0 else -1, 0
        if vertical:
            return 0, 1 if vertical > 0 else -1
        return 0, 0

    def try_move_enemy(self, enemy: dict[str, Any], dx: int, dy: int) -> None:
        nx = int(enemy.get("x", 0)) + dx
        ny = int(enemy.get("y", 0)) + dy
        grid = self.room.get("grid", {})
        columns = int(grid.get("columns", 128))
        rows = int(grid.get("rows", 128))

        blocked = not (0 <= nx < columns and 0 <= ny < rows)
        if not blocked:
            for item in self.items_at(nx, ny):
                if item is enemy:
                    continue
                if item.get("solid", False) or item.get("part_id") == "player":
                    blocked = True
                    break

        if blocked:
            if str(enemy.get("behavior", "")).lower() == "patrol":
                enemy["patrol_direction"] = -int(enemy.get("patrol_direction", 1))
            return

        enemy["x"] = nx
        enemy["y"] = ny

    def enemy_touches_player(self, enemy: dict[str, Any]) -> bool:
        return int(enemy.get("x", -99)) == self.player_x and int(enemy.get("y", -99)) == self.player_y

    def damage_player_from_enemy(self, enemy: dict[str, Any], now: int) -> None:
        if now < self.player_invulnerable_until:
            return

        damage = max(1, int(enemy.get("damage", 1)))
        self.counters["health"] = max(0, int(self.counters.get("health", 0)) - damage)
        self.player_invulnerable_until = now + max(250, int(enemy.get("hit_cooldown", 900)))
        self.status = f"{enemy.get('name', 'Enemy')} hit you for {damage}"
        self.knockback_player(enemy)

        if self.counters["health"] <= 0:
            self.message = "GAME OVER"
            self.status = "Player defeated. Press Esc or B to return."

    def knockback_player(self, enemy: dict[str, Any]) -> None:
        ex, ey = int(enemy.get("x", 0)), int(enemy.get("y", 0))
        dx = 0 if self.player_x == ex else (1 if self.player_x > ex else -1)
        dy = 0 if self.player_y == ey else (1 if self.player_y > ey else -1)
        if abs(dx) >= abs(dy) and dx:
            self.try_move(dx, 0)
        elif dy:
            self.try_move(0, dy)

    def damage_enemy_at_weapon(self, step: int, sword: dict[str, Any]) -> None:
        dx, dy = self.weapon_grid_offset(step)
        target_x = self.player_x + dx
        target_y = self.player_y + dy
        damage = max(1, int(sword.get("damage", 1)))

        for enemy in list(self.enemy_items()):
            if enemy.get("x") != target_x or enemy.get("y") != target_y:
                continue

            enemy["health"] = int(enemy.get("health", 1)) - damage
            self.status = f"Sword hit {enemy.get('name', 'enemy')} for {damage}"

            if enemy["health"] <= 0:
                self.defeat_enemy(enemy)
            break

    def defeat_enemy(self, enemy: dict[str, Any]) -> None:
        actors = self.room.get("layers", {}).get("actors", [])
        if enemy in actors:
            actors.remove(enemy)

        reward = max(0, int(enemy.get("score_reward", 1)))
        self.counters["score"] = int(self.counters.get("score", 0)) + reward
        self.status = f"Defeated {enemy.get('name', 'enemy')}! +{reward} score"

        effect = str(enemy.get("death_effect", "sparkle")).lower()
        emoji = "💥" if effect == "explosion" else "✨"
        self.effects.append({
            "x": int(enemy.get("x", 0)),
            "y": int(enemy.get("y", 0)),
            "emoji": emoji,
            "until": pygame.time.get_ticks() + 550,
        })

        if bool(enemy.get("respawn", False)):
            key = self.enemy_key(enemy)
            spawn = deepcopy(self.enemy_spawn_data.get(key, enemy))
            spawn["health"] = int(spawn.get("max_health", spawn.get("health", 1)))
            self.enemy_respawn_due.append({
                "enemy": spawn,
                "due": pygame.time.get_ticks() + max(500, int(enemy.get("respawn_delay", 3000))),
            })

    def update_respawns(self, now: int) -> None:
        pending: list[dict[str, Any]] = []
        for entry in self.enemy_respawn_due:
            if now >= int(entry.get("due", 0)):
                enemy = deepcopy(entry["enemy"])
                self.room.setdefault("layers", {}).setdefault("actors", []).append(enemy)
                self.status = f"{enemy.get('name', 'Enemy')} respawned"
            else:
                pending.append(entry)
        self.enemy_respawn_due = pending

    def change_room(self, room_id: str, x: int, y: int) -> None:
        super().change_room(room_id, x, y)
        self.enemy_last_move = {}
        self.enemy_spawn_data = {}
        self.enemy_respawn_due = []
        self.capture_enemy_spawns()

    def draw(self, surface, draw_item, colors, fonts) -> None:
        super().draw(surface, draw_item, colors, fonts)
        for effect in self.effects:
            draw_item(
                surface,
                {
                    "x": effect["x"],
                    "y": effect["y"],
                    "emoji": effect["emoji"],
                    "color": [240, 190, 80],
                },
                self.camera_x,
                self.camera_y,
                False,
            )
