# bloomquest_app_v07.py
# run with: imported by bloomquest_v07.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v07.py
# description: Adds automatic gamepad detection and controls to BloomQuest play mode.
# version: 0.7.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, gamepad, controller, joystick, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, USB or Bluetooth gamepad
# notes: D-pad or left stick moves. A interacts. B returns. Start enters Play Mode.
# uuid: bc-bloomquest-app-0007

from __future__ import annotations

import pygame

from editor.bloomquest_app_v06 import BloomQuestAppV06


class BloomQuestAppV07(BloomQuestAppV06):
    """BloomQuest v0.7 with keyboard and gamepad controls."""

    STICK_DEADZONE = 0.55
    MOVE_REPEAT_MS = 150

    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("BloomQuest Engine v0.7")
        pygame.joystick.init()

        self.gamepads: dict[int, pygame.joystick.Joystick] = {}
        self.last_gamepad_move_ms = 0
        self.last_stick_direction = (0, 0)

        self.find_existing_gamepads()
        self.update_gamepad_status()

    def find_existing_gamepads(self) -> None:
        """Open every controller already connected at startup."""
        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.gamepads[joystick.get_instance_id()] = joystick

    def update_gamepad_status(self) -> None:
        """Show a readable connection message in the status bar."""
        if self.gamepads:
            names = ", ".join(gamepad.get_name() for gamepad in self.gamepads.values())
            self.status_message = f"Gamepad connected: {names}"
        else:
            self.status_message = "v0.7 ready. Keyboard active; connect a gamepad anytime."

    def run(self) -> None:
        """Run the editor and poll analog sticks every frame."""
        while self.running:
            self.handle_events()
            self.poll_gamepads()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def handle_events(self) -> None:
        """Handle keyboard, text, mouse, and hot-plugged gamepads."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.JOYDEVICEADDED:
                joystick = pygame.joystick.Joystick(event.device_index)
                joystick.init()
                self.gamepads[joystick.get_instance_id()] = joystick
                self.status_message = f"Gamepad connected: {joystick.get_name()}"

            elif event.type == pygame.JOYDEVICEREMOVED:
                removed = self.gamepads.pop(event.instance_id, None)
                if removed:
                    self.status_message = f"Gamepad disconnected: {removed.get_name()}"

            elif event.type == pygame.JOYBUTTONDOWN:
                self.handle_gamepad_button(event.button)

            elif event.type == pygame.JOYHATMOTION:
                self.handle_hat(event.value)

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

    def handle_gamepad_button(self, button: int) -> None:
        """Map common Xbox-style button numbers to BloomQuest actions."""
        if self.mode == "play":
            if not self.world_play:
                return

            if button == 0:  # A / Cross
                self.world_play.interact()
            elif button in (1, 6):  # B / Circle or Back
                self.exit_play_mode()
            elif button == 7:  # Start / Menu
                self.exit_play_mode()
            return

        if self.overlay:
            if button in (1, 6):
                self.overlay = None
                self.overlay_scroll = 0
            return

        if button == 7:  # Start / Menu
            self.enter_play_mode()
        elif button == 0 and self.selected_instance:
            self.apply_properties()
        elif button in (1, 6):
            self.clear_selection()

    def handle_hat(self, value: tuple[int, int]) -> None:
        """Use the D-pad for grid movement in Play Mode."""
        if self.mode != "play" or not self.world_play:
            return

        horizontal, vertical = value
        if horizontal:
            self.world_play.try_move(horizontal, 0)
        elif vertical:
            self.world_play.try_move(0, -vertical)

        self.last_gamepad_move_ms = pygame.time.get_ticks()

    def poll_gamepads(self) -> None:
        """Poll left analog sticks with a repeat delay for grid movement."""
        if self.mode != "play" or not self.world_play or not self.gamepads:
            self.last_stick_direction = (0, 0)
            return

        gamepad = next(iter(self.gamepads.values()))
        if gamepad.get_numaxes() < 2:
            return

        axis_x = gamepad.get_axis(0)
        axis_y = gamepad.get_axis(1)
        direction = (0, 0)

        if abs(axis_x) >= abs(axis_y) and abs(axis_x) >= self.STICK_DEADZONE:
            direction = (1 if axis_x > 0 else -1, 0)
        elif abs(axis_y) > abs(axis_x) and abs(axis_y) >= self.STICK_DEADZONE:
            direction = (0, 1 if axis_y > 0 else -1)

        now = pygame.time.get_ticks()
        direction_changed = direction != self.last_stick_direction
        repeat_ready = now - self.last_gamepad_move_ms >= self.MOVE_REPEAT_MS

        if direction != (0, 0) and (direction_changed or repeat_ready):
            self.world_play.try_move(*direction)
            self.last_gamepad_move_ms = now

        self.last_stick_direction = direction

    def draw_top_bar(self) -> None:
        """Use the clean v0.6 bar and update only the version label."""
        super().draw_top_bar()

        # Replace the compact title while preserving every button.
        pygame.draw.rect(self.screen, (35, 39, 47), (0, 0, 275, 54))

        from editor.bloomquest_app import MUTED_TEXT, draw_text

        draw_text(self.screen, "BloomQuest v0.7", 14, 5, self.font_large)
        draw_text(self.screen, self.current_room_id, 16, 32, self.font_small, MUTED_TEXT)

    def draw_play_mode(self) -> None:
        """Show both keyboard and gamepad instructions."""
        super().draw_play_mode()

        from editor.bloomquest_app import MUTED_TEXT, TOP_BAR_HEIGHT, draw_text

        draw_text(self.screen, "Gamepad:", 18, TOP_BAR_HEIGHT + 150, self.font_small)
        draw_text(self.screen, "D-pad / Stick = move", 18, TOP_BAR_HEIGHT + 174, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "A = interact", 18, TOP_BAR_HEIGHT + 198, self.font_small, MUTED_TEXT)
        draw_text(self.screen, "B / Start = return", 18, TOP_BAR_HEIGHT + 222, self.font_small, MUTED_TEXT)

        if self.gamepads:
            gamepad_name = next(iter(self.gamepads.values())).get_name()
            draw_text(self.screen, "Connected:", 18, TOP_BAR_HEIGHT + 266, self.font_small)
            draw_text(self.screen, gamepad_name[:25], 18, TOP_BAR_HEIGHT + 290, self.font_small, MUTED_TEXT)

    def help_content(self, page: str) -> list[str]:
        content = super().help_content(page)

        if page == "directions":
            content.extend(
                [
                    "## Gamepad Controls",
                    "22. Connect a USB or Bluetooth controller.",
                    "23. Use the D-pad or left stick to move.",
                    "24. Press A to interact with signs, NPCs, and chests.",
                    "25. Press B or Start to return to Edit Mode.",
                    "26. Press Start in Edit Mode to begin Play Mode.",
                ]
            )
        elif page == "glossary":
            content.extend(
                [
                    "## Gamepad",
                    "A USB or Bluetooth controller used instead of the keyboard.",
                    "## Deadzone",
                    "The center area of an analog stick that ignores tiny accidental movement.",
                ]
            )
        else:
            content.extend(
                [
                    "## Gamepad Controls",
                    "D-pad or left stick: move.",
                    "A: interact. B or Start: return to Edit Mode.",
                    "Start in Edit Mode: begin Play Mode.",
                    "Controllers are detected automatically, including hot-plugged devices.",
                ]
            )

        return content
