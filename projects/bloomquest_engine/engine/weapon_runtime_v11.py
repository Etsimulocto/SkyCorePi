# weapon_runtime_v11.py
# run with: imported by engine/world_play_v11.py
# path: projects/bloomquest_engine/engine/weapon_runtime_v11.py
# description: Projectile and timed area-effect helpers for BloomQuest weapons.
# version: 0.11.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, weapons, projectiles, bombs, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Game-only helpers; no hardware control.
# uuid: bc-bloomquest-weapons-0011

from __future__ import annotations

from typing import Any

import pygame


def make_projectile(player_x: int, player_y: int, facing: tuple[int, int], weapon: dict[str, Any]) -> dict[str, Any]:
    settings = weapon.get("weapon", {})
    dx, dy = facing
    return {
        "x": player_x + dx,
        "y": player_y + dy,
        "dx": dx,
        "dy": dy,
        "emoji": settings.get("projectile_emoji", "•"),
        "damage": max(1, int(weapon.get("damage", 1))),
        "range_left": max(1, int(settings.get("range", 8))),
        "speed_ms": max(35, int(settings.get("speed_ms", 90))),
        "last_move": pygame.time.get_ticks(),
        "name": weapon.get("name", "Projectile"),
    }


def make_bomb(player_x: int, player_y: int, weapon: dict[str, Any]) -> dict[str, Any]:
    settings = weapon.get("weapon", {})
    return {
        "x": player_x,
        "y": player_y,
        "emoji": weapon.get("emoji", "💣"),
        "damage": max(1, int(weapon.get("damage", 3))),
        "radius": max(1, int(settings.get("radius", 1))),
        "trigger_at": pygame.time.get_ticks() + max(250, int(settings.get("fuse_ms", 1200))),
    }
