# bloomquest_v10.py
# run with: python bloomquest_v10.py
# path: projects/bloomquest_engine/bloomquest_v10.py
# description: Launches BloomQuest Engine v0.10 with enemy behavior and combat settings.
# version: 0.10.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, enemies, ai, combat, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, gamepad optional
# notes: Configure enemies in the Actors panel and test them in Play Mode.
# uuid: bc-bloomquest-launcher-0010

from editor.bloomquest_app_v10 import BloomQuestAppV10


if __name__ == "__main__":
    BloomQuestAppV10().run()
