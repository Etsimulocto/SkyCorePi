# world_play_v11.py
# run with: imported by editor/bloomquest_app_v11.py
# path: projects/bloomquest_engine/engine/world_play_v11.py
# description: Multi-weapon runtime with sword, bow, wand, bombs, switching, projectiles, and area effects.
# version: 0.11.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, bow, wand, bombs, projectiles, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Q/E or shoulder buttons switch weapons. Space or X fires.
# uuid: bc-bloomquest-worldplay-0011

from __future__ import annotations

from typing import Any

import pygame

from engine.weapon_runtime_v11 import make_bomb, make_projectile
from engine.world_play_v10 import WorldPlayV10


class WorldPlayV11(WorldPlayV10):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.facing = (1, 0)
        self.weapon_index = 0
        self.projectiles: list[dict[str, Any]] = []
        self.bombs: list[dict[str, Any]] = []
        self.last_weapon_fire_ms = 0
        self.update_weapon_status()

    def equipped_weapons(self) -> list[dict[str, Any]]:
        return [
            item for item in self.room.get("layers", {}).get("weapons", [])
            if item.get("enabled", True) and item.get("weapon")
        ]

    def current_weapon(self) -> dict[str, Any] | None:
        weapons = self.equipped_weapons()
        if not weapons:
            return None
        self.weapon_index %= len(weapons)
        return weapons[self.weapon_index]

    def update_weapon_status(self) -> None:
        weapon = self.current_weapon()
        self.status = (
            f"Weapon: {weapon.get('name', 'Weapon')} | Q/E switch | Space fire"
            if weapon else "No weapon placed in this room."
        )

    def cycle_weapon(self, direction: int) -> None:
        weapons = self.equipped_weapons()
        if not weapons:
            self.status = "No weapons equipped."
            return
        self.weapon_index = (self.weapon_index + direction) % len(weapons)
        self.update_weapon_status()

    def try_move(self, dx: int, dy: int) -> None:
        if dx or dy:
            self.facing = (dx, dy)
        super().try_move(dx, dy)

    def handle_key(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key == pygame.K_q:
            self.cycle_weapon(-1)
            return True
        if event.key == pygame.K_e:
            self.cycle_weapon(1)
            return True
        if event.key == pygame.K_SPACE:
            self.fire_current_weapon()
            return True
        return super().handle_key(event)

    def fire_current_weapon(self) -> None:
        weapon = self.current_weapon()
        if not weapon:
            self.status = "No weapon equipped."
            return

        now = pygame.time.get_ticks()
        settings = weapon.get("weapon", {})
        cooldown = max(0, int(settings.get("cooldown_ms", 350)))
        if now - self.last_weapon_fire_ms < cooldown:
            return
        self.last_weapon_fire_ms = now

        kind = str(settings.get("type", "orbit"))
        if kind == "projectile":
            self.projectiles.append(make_projectile(self.player_x, self.player_y, self.facing, weapon))
            self.status = f"Fired {weapon.get('name', 'weapon')}"
        elif kind == "bomb":
            self.bombs.append(make_bomb(self.player_x, self.player_y, weapon))
            self.status = "Bomb dropped!"
        else:
            self.status = "The sword attacks automatically while selected."

    def update(self) -> None:
        super().update()
        now = pygame.time.get_ticks()
        self.update_projectiles(now)
        self.update_bombs(now)

    def update_projectiles(self, now: int) -> None:
        remaining: list[dict[str, Any]] = []
        for shot in self.projectiles:
            if now - int(shot["last_move"]) < int(shot["speed_ms"]):
                remaining.append(shot)
                continue

            shot["last_move"] = now
            shot["x"] += shot["dx"]
            shot["y"] += shot["dy"]
            shot["range_left"] -= 1

            if self.projectile_hits_enemy(shot):
                continue
            if self.projectile_blocked(shot):
                continue
            if shot["range_left"] > 0:
                remaining.append(shot)
        self.projectiles = remaining

    def projectile_hits_enemy(self, shot: dict[str, Any]) -> bool:
        for enemy in list(self.enemy_items()):
            if enemy.get("x") == shot["x"] and enemy.get("y") == shot["y"]:
                enemy["health"] = int(enemy.get("health", 1)) - int(shot["damage"])
                self.status = f"{shot['name']} hit {enemy.get('name', 'enemy')}"
                if enemy["health"] <= 0:
                    self.defeat_enemy(enemy)
                return True
        return False

    def projectile_blocked(self, shot: dict[str, Any]) -> bool:
        return any(
            item.get("solid", False) and item.get("layer") != "actors"
            for item in self.items_at(int(shot["x"]), int(shot["y"]))
        )

    def update_bombs(self, now: int) -> None:
        remaining: list[dict[str, Any]] = []
        for bomb in self.bombs:
            if now < int(bomb["trigger_at"]):
                remaining.append(bomb)
            else:
                self.trigger_bomb(bomb)
        self.bombs = remaining

    def trigger_bomb(self, bomb: dict[str, Any]) -> None:
        bx, by = int(bomb["x"]), int(bomb["y"])
        radius = int(bomb["radius"])
        damage = int(bomb["damage"])
        self.effects.append({"x": bx, "y": by, "emoji": "💥", "until": pygame.time.get_ticks() + 650})

        for enemy in list(self.enemy_items()):
            distance = abs(int(enemy.get("x", 0)) - bx) + abs(int(enemy.get("y", 0)) - by)
            if distance <= radius:
                enemy["health"] = int(enemy.get("health", 1)) - damage
                if enemy["health"] <= 0:
                    self.defeat_enemy(enemy)
        self.status = "Bomb activated!"

    def equipped_sword(self) -> dict[str, Any] | None:
        weapon = self.current_weapon()
        if weapon and weapon.get("weapon", {}).get("type") == "orbit":
            return weapon
        return None

    def change_room(self, room_id: str, x: int, y: int) -> None:
        super().change_room(room_id, x, y)
        self.projectiles = []
        self.bombs = []
        self.weapon_index = 0
        self.update_weapon_status()

    def draw(self, surface, draw_item, colors, fonts) -> None:
        super().draw(surface, draw_item, colors, fonts)

        for shot in self.projectiles:
            draw_item(surface, {
                "x": shot["x"], "y": shot["y"], "emoji": shot["emoji"], "color": [235, 220, 120]
            }, self.camera_x, self.camera_y, False)

        for bomb in self.bombs:
            draw_item(surface, {
                "x": bomb["x"], "y": bomb["y"], "emoji": bomb["emoji"], "color": [70, 70, 75]
            }, self.camera_x, self.camera_y, False)
