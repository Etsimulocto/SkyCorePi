# bloomquest_v14.py
# run with: python bloomquest_v14.py
# description: Launches BloomQuest v0.14 with project theme and display settings.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v14 import BloomQuestAppV14


if __name__ == "__main__":
    BloomQuestAppV14().run()
