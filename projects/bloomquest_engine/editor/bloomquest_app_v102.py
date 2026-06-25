# bloomquest_app_v102.py
# run with: imported by bloomquest_v102.py
# path: projects/bloomquest_engine/editor/bloomquest_app_v102.py
# description: Adds a movable resizable window with proportional UI scaling and accurate mouse mapping.
# version: 0.10.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, window, resize, scaling, multimonitor, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: The editor renders at 1360x840 internally and scales without distortion.
# uuid: bc-bloomquest-app-0010-2

from __future__ import annotations

import pygame

from editor.bloomquest_app import (
    CANVAS_RIGHT,
    PALETTE_WIDTH,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from editor.bloomquest_app_v10 import BloomQuestAppV10


class BloomQuestAppV102(BloomQuestAppV10):
    """BloomQuest v0.10.2 with a normal movable, scalable window."""

    MIN_WINDOW_WIDTH = 760
    MIN_WINDOW_HEIGHT = 470

    def __init__(self) -> None:
        super().__init__()

        self.logical_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.logical_surface = pygame.Surface(self.logical_size).convert()

        desktop = pygame.display.get_desktop_sizes()
        desktop_width, desktop_height = desktop[0] if desktop else (1280, 720)
        initial_width = min(1100, max(self.MIN_WINDOW_WIDTH, desktop_width - 140))
        initial_height = min(680, max(self.MIN_WINDOW_HEIGHT, desktop_height - 140))

        self.display_surface = pygame.display.set_mode(
            (initial_width, initial_height),
            pygame.RESIZABLE,
        )
        self.screen = self.display_surface
        self.render_rect = pygame.Rect(0, 0, initial_width, initial_height)
        self.last_logical_mouse = (0, 0)

        pygame.display.set_caption("BloomQuest Engine v0.10.2 — Resizable")
        self.status_message = "Resizable window active. Drag the title bar to another monitor."

    def run(self) -> None:
        """Render to a fixed logical canvas, then scale it into the window."""
        while self.running:
            self.handle_events()
            self.poll_gamepads()

            if self.mode == "play" and self.world_play and hasattr(self.world_play, "update"):
                self.world_play.update()

            self.screen = self.logical_surface
            self.draw()

            self.screen = self.display_surface
            self.present_scaled()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def present_scaled(self) -> None:
        """Scale proportionally and center the editor without stretching it."""
        window_width, window_height = self.display_surface.get_size()
        logical_width, logical_height = self.logical_size

        scale = min(window_width / logical_width, window_height / logical_height)
        scaled_width = max(1, round(logical_width * scale))
        scaled_height = max(1, round(logical_height * scale))
        offset_x = (window_width - scaled_width) // 2
        offset_y = (window_height - scaled_height) // 2

        self.render_rect = pygame.Rect(offset_x, offset_y, scaled_width, scaled_height)
        self.display_surface.fill((10, 12, 16))

        scaled = pygame.transform.smoothscale(
            self.logical_surface,
            (scaled_width, scaled_height),
        )
        self.display_surface.blit(scaled, self.render_rect)

    def screen_to_logical(self, position: tuple[int, int]) -> tuple[int, int] | None:
        """Translate real window coordinates into the internal editor coordinates."""
        if not self.render_rect.collidepoint(position):
            return None

        relative_x = position[0] - self.render_rect.x
        relative_y = position[1] - self.render_rect.y

        logical_x = int(relative_x * WINDOW_WIDTH / self.render_rect.width)
        logical_y = int(relative_y * WINDOW_HEIGHT / self.render_rect.height)

        logical_x = max(0, min(WINDOW_WIDTH - 1, logical_x))
        logical_y = max(0, min(WINDOW_HEIGHT - 1, logical_y))
        return logical_x, logical_y

    def handle_events(self) -> None:
        """Handle resize and translate mouse input through the scaled viewport."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                width = max(self.MIN_WINDOW_WIDTH, event.w)
                height = max(self.MIN_WINDOW_HEIGHT, event.h)
                self.display_surface = pygame.display.set_mode(
                    (width, height),
                    pygame.RESIZABLE,
                )
                self.screen = self.display_surface

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

            elif event.type == pygame.MOUSEMOTION:
                logical_position = self.screen_to_logical(event.pos)
                if logical_position is not None:
                    self.last_logical_mouse = logical_position

            elif event.type == pygame.MOUSEBUTTONDOWN:
                logical_position = self.screen_to_logical(event.pos)
                if logical_position is not None:
                    self.last_logical_mouse = logical_position
                    translated = pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN,
                        {
                            "pos": logical_position,
                            "button": event.button,
                            "touch": getattr(event, "touch", False),
                        },
                    )
                    self.handle_click(translated)

            elif event.type == pygame.MOUSEWHEEL:
                self.handle_wheel(event)

    def handle_wheel(self, event: pygame.event.Event) -> None:
        """Scroll the correct logical panel after window scaling."""
        if self.overlay:
            self.overlay_scroll = max(0, self.overlay_scroll - event.y * 30)
            return

        logical_x, _ = self.last_logical_mouse
        if logical_x < PALETTE_WIDTH:
            self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
        elif logical_x >= CANVAS_RIGHT:
            self.properties_scroll = max(0, self.properties_scroll - event.y * 34)
        else:
            self.camera_y = max(0, self.camera_y - event.y * TILE_SIZE)

    def draw_status(self) -> None:
        """Keep the inherited status bar and include the resize hint."""
        super().draw_status()
