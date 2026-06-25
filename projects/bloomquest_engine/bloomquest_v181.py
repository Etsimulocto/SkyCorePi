# bloomquest_v181.py
# run with: python bloomquest_v181.py
# description: Launches BloomQuest v0.18.1 with the illustrated Adventure 001 title cover.

import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
os.environ["SDL_VIDEO_WINDOW_POS"] = "centered,centered"

from editor.bloomquest_app_v181 import BloomQuestAppV181


if __name__ == "__main__":
    BloomQuestAppV181().run()
