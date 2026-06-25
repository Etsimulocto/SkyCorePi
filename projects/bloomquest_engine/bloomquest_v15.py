# bloomquest_v15.py
# run with: python bloomquest_v15.py
# description: Launches BloomQuest v0.15 with premade and random map generation.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v15 import BloomQuestAppV15


if __name__ == "__main__":
    BloomQuestAppV15().run()
