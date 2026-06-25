# bloomquest_v131.py
# run with: python bloomquest_v131.py
# description: Launches BloomQuest v0.13.1 with Decorations visible in Edit Mode.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v131 import BloomQuestAppV131


if __name__ == "__main__":
    BloomQuestAppV131().run()
