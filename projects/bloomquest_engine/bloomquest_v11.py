# bloomquest_v11.py
# run with: python bloomquest_v11.py
# path: projects/bloomquest_engine/bloomquest_v11.py
# description: Launches BloomQuest Engine v0.11 with Sword, Bow, Wand, and Bombs.
# version: 0.11.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, weapons, bow, wand, bombs, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Place weapons in the Weapons panel and switch them during Play Mode.
# uuid: bc-bloomquest-launcher-0011

from editor.bloomquest_app_v11 import BloomQuestAppV11


if __name__ == "__main__":
    BloomQuestAppV11().run()
