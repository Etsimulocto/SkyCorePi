# bloomquest_v13.py
# run with: python bloomquest_v13.py
# description: Launches BloomQuest v0.13 with decorations and atmosphere effects.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v13 import BloomQuestAppV13


if __name__ == "__main__":
    BloomQuestAppV13().run()
