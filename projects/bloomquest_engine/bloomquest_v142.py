# bloomquest_v142.py
# run with: python bloomquest_v142.py
# description: Launches BloomQuest v0.14.2 with visual themes and complete Game Over restart.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v142 import BloomQuestAppV142


if __name__ == "__main__":
    BloomQuestAppV142().run()
