#!/usr/bin/env bash
set -euo pipefail
# Optional isolated runtime: system Python and the basic app stay unchanged.
sudo apt-get install -y python3-venv python3-opencv libgles2
VISION_DIR="$HOME/.local/share/skycorepi/vision-venv"
python3 -m venv --system-site-packages "$VISION_DIR"
"$VISION_DIR/bin/python" -m pip install 'mediapipe==1.0.1' 'numpy<2'
"$VISION_DIR/bin/python" - <<'PY'
from pathlib import Path
import urllib.request
import hashlib
p=Path.home()/'.cache'/'skycorepi'/'gesture_recognizer.task'
p.parent.mkdir(parents=True,exist_ok=True)
url='https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task'
with urllib.request.urlopen(url,timeout=60) as response:
    data=response.read(16*1024*1024)
if hashlib.sha256(data).hexdigest()!='97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482':raise RuntimeError('Gesture model checksum mismatch')
temp=p.with_suffix('.tmp');temp.write_bytes(data);temp.replace(p)
print('Gesture model installed. SHA256:',hashlib.sha256(data).hexdigest())
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
options=vision.GestureRecognizerOptions(base_options=python.BaseOptions(model_asset_path=str(p)))
with vision.GestureRecognizer.create_from_options(options):pass
print('MediaPipe ready. Restart BRO, select Hands mode.')
PY
