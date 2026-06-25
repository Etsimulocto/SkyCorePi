from __future__ import annotations

from copy import deepcopy


class EquipmentPatchV112:
    def equipment_preset(self, part_id: str):
        for part in self.parts:
            if part.get("id") == part_id and part.get("weapon"):
                return part
        return None

    def repair_equipment(self) -> None:
        changed = False
        layers = self.room.setdefault("layers", {})
        placed = list(layers.setdefault("weapons", []))
        placed.extend(layers.setdefault("weapons_effects", []))

        for item in placed:
            preset = self.equipment_preset(str(item.get("part_id", "")))
            if not preset:
                continue
            if not item.get("weapon"):
                item["weapon"] = deepcopy(preset["weapon"])
                changed = True
            if "damage" not in item:
                item["damage"] = int(preset.get("damage", 1))
                changed = True
            if not item.get("emoji"):
                item["emoji"] = preset.get("emoji", "")
                changed = True

        if changed:
            self.room_manager.save(self.room)

    def place_or_select(self, gx: int, gy: int) -> None:
        before = len(self.room.get("layers", {}).get(self.active_layer, []))
        super().place_or_select(gx, gy)
        after = len(self.room.get("layers", {}).get(self.active_layer, []))

        if not self.selected_instance or after <= before:
            return

        preset = self.selected_part
        if preset.get("layer") == "weapons" and preset.get("weapon"):
            self.selected_instance["weapon"] = deepcopy(preset["weapon"])
            self.selected_instance["damage"] = int(preset.get("damage", 1))

    def switch_room(self, room_id: str) -> None:
        super().switch_room(room_id)
        self.repair_equipment()
