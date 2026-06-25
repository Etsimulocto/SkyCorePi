# bloomquest_v161.py
# run with: python bloomquest_v161.py
# description: Launches BloomQuest v0.16.1 with cleaned header spacing.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v161 import BloomQuestAppV161


if __name__ == "__main__":
    BloomQuestAppV161().run()
