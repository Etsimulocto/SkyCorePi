# bloomquest_v09.py
# run with: python bloomquest_v09.py
# path: projects/bloomquest_engine/bloomquest_v09.py
# description: Launches BloomQuest Engine v0.9 with external project workspaces.
# version: 0.9.0
# updated: 2026-06-25
# format: bloomcore/v1.3
# tags: bloomquest, launcher, projects, workspace, pygame
# gpio: none
# dependencies: pygame-ce >= 2.5.7
# author: bloomcraft/sky
# license: MIT
# hardware: Windows PC, Linux PC, Raspberry Pi
# notes: Projects are stored in ~/BloomQuestProjects.
# uuid: bc-bloomquest-launcher-0009

from editor.bloomquest_app_v09 import BloomQuestAppV09


if __name__ == "__main__":
    BloomQuestAppV09().run()
