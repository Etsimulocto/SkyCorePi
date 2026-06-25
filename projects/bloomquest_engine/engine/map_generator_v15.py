# map_generator_v15.py
# run with: imported by editor/bloomquest_app_v15.py
# path: projects/bloomquest_engine/engine/map_generator_v15.py
# description: Generates playable Forest, Village, Dungeon, Cave, Maze, and Arena rooms from a repeatable seed.
# version: 0.15.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, generator, procedural, maps, templates, seed
# gpio: none
# dependencies: Python 3.11+
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Generated rooms always include a player spawn, reachable floor, enemies, treasure, decorations, a weapon, and an exit.
# uuid: bc-bloomquest-map-generator-0015

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any


class BloomQuestMapGenerator:
    """Create compact, playable rooms inside the standard 128x128 BloomQuest grid."""

    STYLES = ("forest", "village", "dungeon", "cave", "maze", "arena")

    def __init__(self, parts: list[dict[str, Any]]) -> None:
        self.parts = {str(part.get("id")): part for part in parts}
        self.instance_counts: dict[str, int] = {}

    def make_item(self, part_id: str, x: int, y: int, **overrides: Any) -> dict[str, Any]:
        part = self.parts.get(part_id)
        if not part:
            raise KeyError(f"Missing generator part: {part_id}")

        self.instance_counts[part_id] = self.instance_counts.get(part_id, 0) + 1
        item = {
            "instance_id": f"{part_id}_{self.instance_counts[part_id]:04d}",
            "part_id": part_id,
            "emoji": part.get("emoji", ""),
            "name": part.get("name", part_id),
            "description": part.get("description", ""),
            "layer": part.get("layer", "map"),
            "x": x,
            "y": y,
            "color": deepcopy(part.get("color", [180, 180, 180])),
            "solid": bool(part.get("solid", False)),
            "enabled": True,
        }
        for key in (
            "action",
            "health",
            "damage",
            "weapon",
            "animation",
            "atmosphere",
            "hidden_in_play",
        ):
            if key in part:
                item[key] = deepcopy(part[key])
        item.update(deepcopy(overrides))
        return item

    def generate(self, room_id: str, style: str, seed: int, width: int = 24, height: int = 20) -> dict[str, Any]:
        style = style.lower()
        if style not in self.STYLES:
            style = "forest"

        rng = random.Random(seed)
        self.instance_counts = {}
        width = max(14, min(36, width))
        height = max(12, min(28, height))

        room = {
            "format": "bloomquest/room-v0.15",
            "room_id": room_id,
            "name": f"Generated {style.title()} — Seed {seed}",
            "grid": {"columns": 128, "rows": 128, "tile_size": 32},
            "layers": {
                "map": [],
                "scene_objects": [],
                "decorations": [],
                "actors": [],
                "weapons": [],
                "weapons_effects": [],
            },
            "counters": {"health": 5, "coins": 0, "score": 0, "keys": 0, "timer": 0},
            "generator": {"style": style, "seed": seed, "width": width, "height": height},
        }

        floor = "dirt" if style in ("dungeon", "cave", "maze", "arena") else "grass"
        for y in range(height):
            for x in range(width):
                room["layers"]["map"].append(self.make_item(floor, x, y))

        if style == "forest":
            self.generate_forest(room, rng, width, height)
        elif style == "village":
            self.generate_village(room, rng, width, height)
        elif style == "dungeon":
            self.generate_dungeon(room, rng, width, height)
        elif style == "cave":
            self.generate_cave(room, rng, width, height)
        elif style == "maze":
            self.generate_maze(room, rng, width, height)
        else:
            self.generate_arena(room, rng, width, height)

        self.add_required_gameplay(room, rng, width, height, style)
        return room

    def border(self, room: dict[str, Any], width: int, height: int, part_id: str = "wall", gap: tuple[int, int] | None = None) -> None:
        for x in range(width):
            for y in (0, height - 1):
                if gap != (x, y):
                    room["layers"]["map"].append(self.make_item(part_id, x, y))
        for y in range(1, height - 1):
            for x in (0, width - 1):
                if gap != (x, y):
                    room["layers"]["map"].append(self.make_item(part_id, x, y))

    @staticmethod
    def blocked(room: dict[str, Any], x: int, y: int) -> bool:
        for layer in ("map", "scene_objects"):
            for item in room["layers"].get(layer, []):
                if item.get("x") == x and item.get("y") == y and item.get("solid"):
                    return True
        return False

    def safe_open_cells(self, room: dict[str, Any], width: int, height: int) -> list[tuple[int, int]]:
        occupied = {
            (int(item.get("x", -1)), int(item.get("y", -1)))
            for layer in room["layers"].values()
            for item in layer
            if item.get("layer") != "map"
        }
        return [
            (x, y)
            for y in range(2, height - 2)
            for x in range(2, width - 2)
            if not self.blocked(room, x, y) and (x, y) not in occupied
        ]

    def add_required_gameplay(self, room: dict[str, Any], rng: random.Random, width: int, height: int, style: str) -> None:
        spawn = (2, 2)
        room["layers"]["actors"].append(self.make_item("player", *spawn))

        exit_x, exit_y = width - 2, height - 2
        room["layers"]["scene_objects"].append(
            self.make_item(
                "door",
                exit_x,
                exit_y,
                action={
                    "trigger": "player_touch",
                    "type": "show_text",
                    "text": "This exit can be linked to another room in Properties.",
                },
            )
        )

        cells = self.safe_open_cells(room, width, height)
        rng.shuffle(cells)

        weapon_id = rng.choice(("sword", "bow", "wand", "bomb"))
        if cells:
            room["layers"]["weapons"].append(self.make_item(weapon_id, *cells.pop()))

        enemy_count = 5 if style != "arena" else 9
        for index in range(enemy_count):
            if not cells:
                break
            enemy_id = "slime" if index % 2 == 0 else "bat"
            behavior = "chase" if style in ("dungeon", "arena", "maze") else rng.choice(("wander", "patrol", "chase"))
            room["layers"]["actors"].append(
                self.make_item(
                    enemy_id,
                    *cells.pop(),
                    behavior=behavior,
                    move_delay=rng.choice((280, 360, 440)),
                    detection_range=rng.choice((5, 6, 7)),
                    hit_cooldown=900,
                    score_reward=1,
                    death_effect=rng.choice(("sparkle", "explosion")),
                    respawn=False,
                    max_health=int(self.parts[enemy_id].get("health", 2)),
                )
            )

        for collectible in ("coin", "coin", "coin", "heart", "key"):
            if cells:
                room["layers"]["scene_objects"].append(self.make_item(collectible, *cells.pop()))

    def generate_forest(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "tree", gap=(width - 2, height - 1))
        reserved = {(2, 2), (width - 2, height - 2)}
        for _ in range((width * height) // 10):
            x, y = rng.randrange(2, width - 2), rng.randrange(2, height - 2)
            if (x, y) not in reserved and not self.blocked(room, x, y):
                room["layers"]["scene_objects"].append(self.make_item(rng.choice(("tree", "rock")), x, y))
        for _ in range(24):
            x, y = rng.randrange(1, width - 1), rng.randrange(1, height - 1)
            room["layers"]["decorations"].append(self.make_item(rng.choice(("flower", "grass_tuft", "mushroom", "fallen_leaves")), x, y))
        room["layers"]["decorations"].append(self.make_item("fireflies_atmosphere", 1, 1))

    def generate_village(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "wall", gap=(width - 2, height - 1))
        road_y = height // 2
        for x in range(1, width - 1):
            room["layers"]["map"].append(self.make_item("dirt", x, road_y))
        for house_x in (4, 10, 16):
            if house_x + 3 >= width - 1:
                continue
            for x in range(house_x, house_x + 4):
                for y in (3, 7):
                    room["layers"]["scene_objects"].append(self.make_item("wall", x, y))
            for y in range(4, 7):
                room["layers"]["scene_objects"].append(self.make_item("wall", house_x, y))
                room["layers"]["scene_objects"].append(self.make_item("wall", house_x + 3, y))
            room["layers"]["scene_objects"].append(self.make_item("door", house_x + 1, 7))
        for _ in range(18):
            room["layers"]["decorations"].append(self.make_item(rng.choice(("flower", "grass_tuft", "puddle")), rng.randrange(1, width - 1), rng.randrange(1, height - 1)))
        room["layers"]["actors"].append(self.make_item("villager", width // 2, road_y - 1))

    def generate_dungeon(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "wall", gap=(width - 2, height - 1))
        for x in range(5, width - 3, 6):
            for y in range(2, height - 2):
                if y not in (height // 3, 2 * height // 3):
                    room["layers"]["scene_objects"].append(self.make_item("wall", x, y))
        for _ in range(14):
            room["layers"]["decorations"].append(self.make_item(rng.choice(("torch", "bones", "rune")), rng.randrange(2, width - 2), rng.randrange(2, height - 2)))

    def generate_cave(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "rock", gap=(width - 2, height - 1))
        for _ in range((width * height) // 8):
            x, y = rng.randrange(2, width - 2), rng.randrange(2, height - 2)
            if abs(x - 2) + abs(y - 2) > 5 and abs(x - (width - 2)) + abs(y - (height - 2)) > 5:
                room["layers"]["scene_objects"].append(self.make_item("rock", x, y))
        for _ in range(16):
            room["layers"]["decorations"].append(self.make_item(rng.choice(("puddle", "mushroom", "rune", "bones")), rng.randrange(2, width - 2), rng.randrange(2, height - 2)))

    def generate_maze(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "wall", gap=(width - 2, height - 1))
        for x in range(4, width - 2, 4):
            gap_y = rng.randrange(2, height - 2)
            for y in range(1, height - 1):
                if y != gap_y:
                    room["layers"]["scene_objects"].append(self.make_item("wall", x, y))
        for y in range(5, height - 2, 5):
            gap_x = rng.randrange(2, width - 2)
            for x in range(1, width - 1):
                if x != gap_x and x % 4 != 0:
                    room["layers"]["scene_objects"].append(self.make_item("wall", x, y))
        for _ in range(12):
            room["layers"]["decorations"].append(self.make_item(rng.choice(("rune", "torch", "bones")), rng.randrange(2, width - 2), rng.randrange(2, height - 2)))

    def generate_arena(self, room: dict[str, Any], rng: random.Random, width: int, height: int) -> None:
        self.border(room, width, height, "wall", gap=(width - 2, height - 1))
        center_x, center_y = width // 2, height // 2
        for dx, dy in ((-5, -3), (5, -3), (-5, 3), (5, 3), (0, -5), (0, 5)):
            room["layers"]["scene_objects"].append(self.make_item("rock", center_x + dx, center_y + dy))
        for _ in range(18):
            room["layers"]["decorations"].append(self.make_item(rng.choice(("torch", "rune", "bones")), rng.randrange(2, width - 2), rng.randrange(2, height - 2)))
