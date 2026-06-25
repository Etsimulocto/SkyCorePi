# bloomquest_app_v103.py
# run with: imported by bloomquest_v103.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v103.py
# description: Adds a clickable dropdown menu for enemy behavior selection.
# version: 0.10.3
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, enemies, behavior, dropdown, ui, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Behavior choices are Idle, Patrol, Wander, and Chase.
# uuid: bc-bloomquest-app-0010-3

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    CANVAS_RIGHT,
    GRID_LINE,
    PANEL_ALT,
    PROPERTIES_WIDTH,
    TEXT,
)
from editor.bloomquest_app_v102 import BloomQuestAppV102


class BloomQuestAppV103(BloomQuestAppV102):
    """BloomQuest v0.10.3 with a real enemy behavior dropdown."""

    BEHAVIOR_OPTIONS = ("idle", "patrol", "wander", "chase")

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.10.3 — Behavior Dropdown")
        self.behavior_dropdown_open = False
        self.behavior_option_rects: list[tuple[str, pygame.Rect]] = []
        self.status_message = "Click Behavior and choose Idle, Patrol, Wander, or Chase."

    def handle_click(self, event: pygame.event.Event) -> None:
        """Handle dropdown options before normal editor clicks."""
        if self.mode == "edit" and not self.overlay:
            x, y = event.pos

            if self.behavior_dropdown_open:
                for option, rect in self.behavior_option_rects:
                    if rect.collidepoint(x, y):
                        field = self.field_by_key.get("behavior")
                        if field:
                            field.value = option
                            field.active = False
                            self.status_message = f"Enemy behavior set to {option.title()}"
                        self.behavior_dropdown_open = False
                        return

                self.behavior_dropdown_open = False

            behavior_field = self.field_by_key.get("behavior")
            if behavior_field and behavior_field.rect.collidepoint(x, y):
                for field in self.fields:
                    field.active = False
                self.behavior_dropdown_open = True
                self.status_message = "Choose an enemy behavior."
                return

        super().handle_click(event)

    def clear_selection(self) -> None:
        self.behavior_dropdown_open = False
        self.behavior_option_rects = []
        super().clear_selection()

    def draw_properties(self) -> None:
        """Draw normal properties, then place the behavior menu above them."""
        super().draw_properties()
        self.behavior_option_rects = []

        if not self.behavior_dropdown_open:
            return

        behavior_field = self.field_by_key.get("behavior")
        if not behavior_field or behavior_field.rect.width <= 0:
            self.behavior_dropdown_open = False
            return

        menu_x = behavior_field.rect.x
        menu_y = behavior_field.rect.bottom + 4
        menu_width = behavior_field.rect.width
        option_height = 34
        menu_height = option_height * len(self.BEHAVIOR_OPTIONS)

        # If the menu would run below the window, open it upward instead.
        if menu_y + menu_height > self.screen.get_height() - 34:
            menu_y = behavior_field.rect.y - menu_height - 4

        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(self.screen, (24, 28, 34), menu_rect, border_radius=6)
        pygame.draw.rect(self.screen, ACCENT, menu_rect, 2, border_radius=6)

        current = behavior_field.value.strip().lower()
        for index, option in enumerate(self.BEHAVIOR_OPTIONS):
            rect = pygame.Rect(menu_x + 2, menu_y + index * option_height + 2, menu_width - 4, option_height - 2)
            selected = option == current
            pygame.draw.rect(
                self.screen,
                ACCENT if selected else PANEL_ALT,
                rect,
                border_radius=4,
            )
            label = self.font_small.render(
                option.title(),
                True,
                BACKGROUND if selected else TEXT,
            )
            self.screen.blit(label, label.get_rect(midleft=(rect.x + 12, rect.centery)))
            self.behavior_option_rects.append((option, rect))

        # Redraw a small arrow on the behavior field so it reads as a dropdown.
        arrow = self.font_small.render("▼", True, TEXT)
        self.screen.blit(
            arrow,
            arrow.get_rect(midright=(behavior_field.rect.right - 10, behavior_field.rect.centery)),
        )

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Behavior Dropdown",
                    "40. Select an enemy and click its Behavior field.",
                    "41. Choose Idle, Patrol, Wander, or Chase from the menu.",
                    "42. Click Apply Changes to save the selection.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Dropdown Menu",
                    "A clickable list of valid choices that avoids typing mistakes.",
                ]
            )
        else:
            content.extend(
                [
                    "## Enemy Behavior Dropdown",
                    "Behavior is selected from a menu instead of typed manually.",
                    "Available choices: Idle, Patrol, Wander, and Chase.",
                ]
            )

        return content
