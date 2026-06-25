# bloomquest_v06.py
# run with: python bloomquest_v06.py
# path: projects/bloomquest_engine/bloomquest_v06.py
# description: Launches BloomQuest Engine v0.6 with Windows emoji input support.
# version: 0.6.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, emoji, unicode, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, or Raspberry Pi
# notes: Click Emoji / Symbol and press Win + period.
# uuid: bc-bloomquest-launcher-0006

from editor.bloomquest_app_v06 import BloomQuestAppV06


if __name__ == "__main__":
    BloomQuestAppV06().run()
