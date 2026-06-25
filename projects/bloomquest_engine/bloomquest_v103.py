# bloomquest_v103.py
# run with: python bloomquest_v103.py
# path: projects/bloomquest_engine/bloomquest_v103.py
# description: Launches BloomQuest Engine v0.10.3 with enemy behavior dropdown controls.
# version: 0.10.3
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, behavior, dropdown, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Click an enemy Behavior field and choose from the dropdown.
# uuid: bc-bloomquest-launcher-0010-3

from editor.bloomquest_app_v103 import BloomQuestAppV103


if __name__ == "__main__":
    BloomQuestAppV103().run()
