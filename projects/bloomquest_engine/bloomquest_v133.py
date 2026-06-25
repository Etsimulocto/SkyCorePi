# bloomquest_v133.py
# run with: python bloomquest_v133.py
# description: Launches BloomQuest v0.13.3 with corrected toolbar spacing.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v133 import BloomQuestAppV133


if __name__ == "__main__":
    BloomQuestAppV133().run()
