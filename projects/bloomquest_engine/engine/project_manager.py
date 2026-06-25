# project_manager.py
# run with: imported by editor/bloomquest_app_v09.py
# path: projects/bloomquest_engine/engine/project_manager.py
# description: Creates and manages BloomQuest user projects outside the Git repository.
# version: 0.9.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, projects, migration, json, safety
# gpio: none
# dependencies: Python 3.11+
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Projects default to ~/BloomQuestProjects so Git updates cannot overwrite user data.
# uuid: bc-bloomquest-projectmanager-0009

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProjectManager:
    """Manage self-contained BloomQuest projects outside the engine repo."""

    def __init__(self, engine_root: Path) -> None:
        self.engine_root = engine_root
        self.projects_root = Path.home() / "BloomQuestProjects"
        self.projects_root.mkdir(parents=True, exist_ok=True)

        self.engine_parts_file = engine_root / "data" / "parts" / "parts_library.json"
        self.engine_rooms_dir = engine_root / "data" / "rooms"

    @staticmethod
    def safe_slug(name: str) -> str:
        cleaned = "".join(character if character.isalnum() else "_" for character in name.strip())
        cleaned = "_".join(piece for piece in cleaned.split("_") if piece)
        return cleaned or "My_Adventure"

    def project_dir(self, project_id: str) -> Path:
        return self.projects_root / self.safe_slug(project_id)

    def project_file(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "project.json"

    def rooms_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "rooms"

    def parts_file(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "parts_library.json"

    def saves_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "saves"

    def exports_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "exports"

    def list_projects(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for project_json in sorted(self.projects_root.glob("*/project.json")):
            try:
                with project_json.open("r", encoding="utf-8") as handle:
                    project = json.load(handle)
                project["path"] = str(project_json.parent)
                projects.append(project)
            except (OSError, json.JSONDecodeError):
                continue
        return sorted(projects, key=lambda item: item.get("updated_at", ""), reverse=True)

    def next_project_id(self) -> str:
        existing = {project.get("project_id", "") for project in self.list_projects()}
        number = 1
        while f"Adventure_{number:03d}" in existing:
            number += 1
        return f"Adventure_{number:03d}"

    def create_project(self, name: str | None = None, migrate_engine_data: bool = False) -> dict[str, Any]:
        project_id = self.safe_slug(name or self.next_project_id())
        base = self.project_dir(project_id)

        if base.exists() and self.project_file(project_id).exists():
            return self.load_project(project_id)

        self.rooms_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.saves_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.exports_dir(project_id).mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()
        project = {
            "format": "bloomquest/project-v0.9",
            "project_id": project_id,
            "name": (name or project_id).replace("_", " "),
            "start_room": "room_001",
            "created_at": now,
            "updated_at": now,
        }

        with self.project_file(project_id).open("w", encoding="utf-8") as handle:
            json.dump(project, handle, indent=2, ensure_ascii=False)

        if self.engine_parts_file.exists():
            shutil.copy2(self.engine_parts_file, self.parts_file(project_id))
        else:
            with self.parts_file(project_id).open("w", encoding="utf-8") as handle:
                json.dump({"format": "bloomquest/parts-v0.2", "tile_size": 32, "parts": []}, handle, indent=2)

        if migrate_engine_data and self.engine_rooms_dir.exists():
            copied = False
            for source in self.engine_rooms_dir.glob("room_*.json"):
                shutil.copy2(source, self.rooms_dir(project_id) / source.name)
                copied = True
            if not copied:
                self.write_blank_room(project_id, "room_001")
        else:
            self.write_blank_room(project_id, "room_001")

        return project

    def ensure_first_project(self) -> dict[str, Any]:
        projects = self.list_projects()
        if projects:
            return projects[0]
        return self.create_project("My_Adventure", migrate_engine_data=True)

    def load_project(self, project_id: str) -> dict[str, Any]:
        with self.project_file(project_id).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_project(self, project: dict[str, Any]) -> None:
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        with self.project_file(project["project_id"]).open("w", encoding="utf-8") as handle:
            json.dump(project, handle, indent=2, ensure_ascii=False)

    def duplicate_project(self, project_id: str) -> dict[str, Any]:
        source = self.project_dir(project_id)
        new_id = self.next_project_id()
        destination = self.project_dir(new_id)
        shutil.copytree(source, destination)

        project = self.load_project(new_id)
        project["project_id"] = new_id
        project["name"] = f"{project.get('name', project_id)} Copy"
        now = datetime.now(timezone.utc).isoformat()
        project["created_at"] = now
        project["updated_at"] = now
        self.save_project(project)
        return project

    def write_blank_room(self, project_id: str, room_id: str) -> None:
        room = {
            "format": "bloomquest/room-v0.9",
            "room_id": room_id,
            "name": room_id.replace("_", " ").title(),
            "grid": {"columns": 128, "rows": 128, "tile_size": 32},
            "layers": {
                "map": [],
                "scene_objects": [],
                "actors": [],
                "weapons": [],
                "weapons_effects": [],
            },
            "counters": {"health": 3, "coins": 0, "score": 0, "keys": 0, "timer": 0},
        }
        with (self.rooms_dir(project_id) / f"{room_id}.json").open("w", encoding="utf-8") as handle:
            json.dump(room, handle, indent=2, ensure_ascii=False)
