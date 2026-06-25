# bloomquest_v05.py
# run with: python bloomquest_v05.py
# path: projects/bloomquest_engine/bloomquest_v05.py
# description: Launches BloomQuest Engine v0.5 with custom reusable part creation.
# version: 0.5.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, custom-parts, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Custom parts are saved into data/parts/parts_library.json.
# uuid: bc-bloomquest-launcher-0005

from editor.bloomquest_app_v05 import BloomQuestAppV05


if __name__ == "__main__":
    BloomQuestAppV05().run()
