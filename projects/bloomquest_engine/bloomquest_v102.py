# bloomquest_v102.py
# run with: python bloomquest_v102.py
# path: projects/bloomquest_engine/bloomquest_v102.py
# description: Launches BloomQuest Engine v0.10.2 with a movable resizable window.
# version: 0.10.2
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, resize, scaling, multimonitor, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Drag the normal title bar between monitors and resize from any edge.
# uuid: bc-bloomquest-launcher-0010-2

from editor.bloomquest_app_v102 import BloomQuestAppV102


if __name__ == "__main__":
    BloomQuestAppV102().run()
