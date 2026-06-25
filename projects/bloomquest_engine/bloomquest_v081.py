# bloomquest_v081.py
# run with: python bloomquest_v081.py
# path: projects/bloomquest_engine/bloomquest_v081.py
# description: Launches BloomQuest Engine v0.8.1 with the Weapons palette fix.
# version: 0.8.1
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, weapons, palette, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Dedicated Weapons and Effects palettes are enabled.
# uuid: bc-bloomquest-launcher-0008-1

from editor.bloomquest_app_v081 import BloomQuestAppV081


if __name__ == "__main__":
    BloomQuestAppV081().run()
