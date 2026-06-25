# bloomquest_v16.py
# run with: python bloomquest_v16.py
# description: Launches BloomQuest v0.16 with title screen, objectives, pause menu, and victory screen.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v16 import BloomQuestAppV16


if __name__ == "__main__":
    BloomQuestAppV16().run()
