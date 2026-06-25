# bloomquest_v132.py
# run with: python bloomquest_v132.py
# description: Launches BloomQuest v0.13.2 using the full resizable window.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v132 import BloomQuestAppV132


if __name__ == "__main__":
    BloomQuestAppV132().run()
