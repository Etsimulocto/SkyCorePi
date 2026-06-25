# bloomquest_v112.py
# run with: python bloomquest_v112.py
# description: Launches BloomQuest v0.11.2 centered on the active display.

import os

# These must be set before pygame creates its first window.
os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v112 import BloomQuestAppV112


if __name__ == "__main__":
    BloomQuestAppV112().run()
