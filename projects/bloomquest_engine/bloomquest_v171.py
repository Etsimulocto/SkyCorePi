# bloomquest_v171.py
# run with: python bloomquest_v171.py
# description: Launches BloomQuest v0.17.1 with cinematic overlays and dynamic lighting.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v171 import BloomQuestAppV171


if __name__ == "__main__":
    BloomQuestAppV171().run()
