# bloomquest_app_v06.py
# run with: imported by bloomquest_v06.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v06.py
# description: Adds proper Unicode TEXTINPUT handling for Windows emoji picker and clipboard paste.
# version: 0.6.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, emoji, unicode, textinput, windows, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Click Emoji / Symbol, press Win + period, then choose an emoji.
# uuid: bc-bloomquest-app-0006

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    ACCENT,
    BACKGROUND,
    LAYER_LABELS,
    LAYER_ORDER,
    MUTED_TEXT,
    PANEL,
    PANEL_ALT,
    TEXT,
    TOP_BAR_HEIGHT,
    draw_text,
)
from editor.bloomquest_app_v05 import BloomQuestAppV05


class BloomQuestAppV06(BloomQuestAppV05):
    """BloomQuest v0.6 with native Unicode and emoji text input."""

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.6")
        pygame.key.start_text_input()

        try:
            pygame.scrap.init()
        except pygame.error:
            pass

        self.status_message = "v0.6 ready. Click Emoji / Symbol, then press Win + ."

    def active_text_field(self):
        return next((field for field in self.fields if field.active), None)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.TEXTINPUT:
                field = self.active_text_field()
                if field is not None and not field.numeric:
                    field.value += event.text
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event)
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_wheel(event)

    def handle_key(self, event: pygame.event.Event) -> None:
        field = self.active_text_field()

        if field is not None:
            control = bool(event.mod & pygame.KMOD_CTRL)

            if control and event.key == pygame.K_v:
                self.paste_into_field(field)
                return
            if event.key == pygame.K_BACKSPACE:
                field.value = field.value[:-1]
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if field.multiline:
                    field.value += " "
                else:
                    field.active = False
                return
            if event.key == pygame.K_TAB:
                field.active = False
                return
            if field.numeric and event.unicode:
                if event.unicode.isdigit() or (event.unicode == "-" and not field.value):
                    field.value += event.unicode
                return
            return

        super().handle_key(event)

    def paste_into_field(self, field) -> None:
        try:
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if not raw:
                return

            if isinstance(raw, bytes):
                text = raw.decode("utf-8", errors="ignore").replace("\x00", "")
            else:
                text = str(raw)

            if field.numeric:
                allowed = "".join(character for character in text if character.isdigit() or character == "-")
                field.value += allowed
            else:
                field.value += text
        except pygame.error:
            self.status_message = "Clipboard paste was unavailable. Win + . should still work."

    def draw_top_bar(self) -> None:
        """Draw the entire top bar cleanly so no inherited title remains."""
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))

        # Compact two-line title stays inside the reserved left area.
        draw_text(self.screen, "BloomQuest v0.6", 14, 5, self.font_large)
        draw_text(self.screen, self.current_room_id, 16, 32, self.font_small, MUTED_TEXT)

        if self.mode != "edit":
            return

        # Layer controls begin after the complete title area.
        button_x = 280
        for layer in LAYER_ORDER:
            rect = pygame.Rect(button_x, 10, 140, 34)
            active = layer == self.active_layer
            pygame.draw.rect(self.screen, ACCENT if active else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(
                LAYER_LABELS[layer],
                True,
                BACKGROUND if active else TEXT,
            )
            self.screen.blit(image, image.get_rect(center=rect.center))
            button_x += 146

        for rect, label in (
            (self.rooms_button, "Rooms"),
            (self.help_button, "Help"),
            (self.play_button, "▶ Play"),
        ):
            is_play = label == "▶ Play"
            pygame.draw.rect(self.screen, ACCENT if is_play else PANEL_ALT, rect, border_radius=6)
            image = self.font_small.render(label, True, BACKGROUND if is_play else TEXT)
            self.screen.blit(image, image.get_rect(center=rect.center))

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Add an Emoji on Windows",
                    "18. Click the Emoji / Symbol field.",
                    "19. Press the Windows key and period together.",
                    "20. Choose an emoji from the Windows panel.",
                    "21. Ctrl+V also supports copied emoji.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Unicode Input",
                    "Text input that supports emoji and symbols from many languages.",
                ]
            )
        else:
            content.extend(
                [
                    "## Windows Emoji Input",
                    "Click Emoji / Symbol, press Win + period, and choose an emoji.",
                    "You can also copy an emoji and paste it with Ctrl+V.",
                ]
            )

        return content
