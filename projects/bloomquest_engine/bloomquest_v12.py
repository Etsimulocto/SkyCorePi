# bloomquest_v12.py
# run with: python bloomquest_v12.py
# description: Launches BloomQuest v0.12 with editable weapon properties.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v12 import BloomQuestAppV12


if __name__ == "__main__":
    BloomQuestAppV12().run()
