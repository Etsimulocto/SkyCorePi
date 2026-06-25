# bloomquest_v08.py
# run with: python bloomquest_v08.py
# path: projects/bloomquest_engine/bloomquest_v08.py
# description: Launches BloomQuest Engine v0.8 with a Weapons panel and orbiting sword combat.
# version: 0.8.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, weapons, sword, combat, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi, gamepad optional
# notes: Place a Sword in Weapons to equip the player.
# uuid: bc-bloomquest-launcher-0008

from editor.bloomquest_app_v08 import BloomQuestAppV08


if __name__ == "__main__":
    BloomQuestAppV08().run()
