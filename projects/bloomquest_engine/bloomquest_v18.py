# bloomquest_v18.py
# run with: python bloomquest_v18.py
# description: Launches BloomQuest v0.18 with touch-to-reveal exploration fog.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v18 import BloomQuestAppV18


if __name__ == "__main__":
    BloomQuestAppV18().run()
