# bloomquest_v07.py
# run with: python bloomquest_v07.py
# path: projects/bloomquest_engine/bloomquest_v07.py
# description: Launches BloomQuest Engine v0.7 with automatic gamepad controls.
# version: 0.7.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, gamepad, controller, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, USB or Bluetooth gamepad
# notes: D-pad or left stick moves. A interacts. B returns. Start enters Play Mode.
# uuid: bc-bloomquest-launcher-0007

from editor.bloomquest_app_v07 import BloomQuestAppV07


if __name__ == "__main__":
    BloomQuestAppV07().run()
