# room_manager.py
# run with: imported by editor/bloomquest_app.py
# path: projects/bloomquest_engine/engine/room_manager.py
# description: Creates, lists, loads, saves, and duplicates BloomQuest JSON rooms.
# version: 0.1.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, rooms, json, manager
# gpio: none
# dependencies: Python 3.11+
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Room IDs use room_001 style names.
# uuid: bc-bloomquest-roommanager-0001

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

LAYER_ORDER = ["map", "scene_objects", "actors", "weapons_effects"]


class RoomManager:
    def __init__(self, rooms_dir: Path, columns: int = 128, rows: int = 128, tile_size: int = 32) -> None:
        self.rooms_dir = rooms_dir
        self.columns = columns
        self.rows = rows
        self.tile_size = tile_size
        self.rooms_dir.mkdir(parents=True, exist_ok=True)

    def list_room_ids(self) -> list[str]:
        return sorted(path.stem for path in self.rooms_dir.glob("room_*.json"))

    def next_room_id(self) -> str:
        used = set(self.list_room_ids())
        number = 1
        while f"room_{number:03d}" in used:
            number += 1
        return f"room_{number:03d}"

    def room_path(self, room_id: str) -> Path:
        safe_id = room_id.strip().replace(" ", "_")
        if not safe_id.startswith("room_"):
            safe_id = f"room_{safe_id}"
        return self.rooms_dir / f"{safe_id}.json"

    def blank_room(self, room_id: str, name: str | None = None) -> dict[str, Any]:
        return {
            "format": "bloomquest/room-v0.4",
            "room_id": room_id,
            "name": name or room_id.replace("_", " ").title(),
            "grid": {"columns": self.columns, "rows": self.rows, "tile_size": self.tile_size},
            "layers": {layer: [] for layer in LAYER_ORDER},
            "counters": {"health": 3, "coins": 0, "score": 0, "keys": 0, "timer": 0},
        }

    def normalize(self, room: dict[str, Any]) -> dict[str, Any]:
        room.setdefault("format", "bloomquest/room-v0.4")
        room.setdefault("room_id", "room_001")
        room.setdefault("name", room["room_id"])
        room.setdefault("grid", {"columns": self.columns, "rows": self.rows, "tile_size": self.tile_size})
        room.setdefault("layers", {})
        for layer in LAYER_ORDER:
            room["layers"].setdefault(layer, [])
        room.setdefault("counters", {})
        for key, value in {"health": 3, "coins": 0, "score": 0, "keys": 0, "timer": 0}.items():
            room["counters"].setdefault(key, value)
        return room

    def load(self, room_id: str) -> dict[str, Any]:
        path = self.room_path(room_id)
        if not path.exists():
            room = self.blank_room(room_id)
            self.save(room)
            return room
        with path.open("r", encoding="utf-8") as handle:
            return self.normalize(json.load(handle))

    def save(self, room: dict[str, Any]) -> Path:
        room = self.normalize(room)
        path = self.room_path(room["room_id"])
        with path.open("w", encoding="utf-8") as handle:
            json.dump(room, handle, indent=2, ensure_ascii=False)
        return path

    def create(self) -> dict[str, Any]:
        room = self.blank_room(self.next_room_id())
        self.save(room)
        return room

    def duplicate(self, room: dict[str, Any]) -> dict[str, Any]:
        copy_room = deepcopy(room)
        copy_room["room_id"] = self.next_room_id()
        copy_room["name"] = f"{room.get('name', room.get('room_id', 'Room'))} Copy"
        self.save(copy_room)
        return copy_room
