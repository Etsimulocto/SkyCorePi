# bloomquest_v141.py
# run with: python bloomquest_v141.py
# description: Launches BloomQuest v0.14.1 with a visual theme color picker.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v141 import BloomQuestAppV141


if __name__ == "__main__":
    BloomQuestAppV141().run()
