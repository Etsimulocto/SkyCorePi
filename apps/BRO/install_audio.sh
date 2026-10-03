#!/usr/bin/env bash
set -euo pipefail
# Opt out before ONNX Runtime initializes, including model downloads/checks.
export ORT_DISABLE_TELEMETRY=1
sudo apt-get install -y python3-venv libportaudio2
AUDIO_DIR="$HOME/.local/share/skycorepi/audio-venv"
VOICE_DIR="$HOME/.cache/skycorepi/audio/voices"
python3 -m venv --system-site-packages "$AUDIO_DIR"
"$AUDIO_DIR/bin/python" -m pip install 'piper-tts==1.8.0' 'vosk==0.3.45' 'sounddevice==0.5.6' 'numpy<2'
mkdir -p "$VOICE_DIR"
"$AUDIO_DIR/bin/python" -m piper.download_voices --data-dir "$VOICE_DIR" en_US-lessac-medium
"$AUDIO_DIR/bin/python" - <<'PY'
from pathlib import Path
import tempfile
import urllib.request
import zipfile
from piper import PiperVoice
from vosk import Model,SetLogLevel
root=Path.home()/'.cache'/'skycorepi'/'audio'
target=root/'vosk-model-small-en-us-0.15'
if not target.is_dir():
    with tempfile.TemporaryDirectory(dir=root) as directory:
        archive=Path(directory)/'model.zip'
        with urllib.request.urlopen('https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',timeout=60) as response,archive.open('wb') as output:
            total=0
            while data:=response.read(1024*1024):
                total+=len(data)
                if total>80*1024*1024:raise RuntimeError('Recognition model download exceeds limit')
                output.write(data)
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>300*1024*1024:raise RuntimeError('Recognition model extraction exceeds limit')
            for i in z.infolist():
                name=Path(i.filename)
                if name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0]!=target.name:raise RuntimeError('Invalid model archive path')
            z.extractall(directory)
        (Path(directory)/target.name).rename(target)
PiperVoice.load(str(root/'voices'/'en_US-lessac-medium.onnx'))
SetLogLevel(-1);Model(str(target))
print('Audio ready: Piper voice + Vosk English model. Restart BRO and Detect / rescan audio.')
PY
