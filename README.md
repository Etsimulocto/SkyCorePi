# SkyCorePi / BRO 0.8.1

BRO is our robot interface development console on Raspberry Pi: an animated face, physical controls, local AI conversation, live camera preview, tracking, hand signals, and copyable diagnostics. We are working out the interface before building the robot body.

Sky, Cold, Monday, and GRIT load their original identity cards from `characters/`. Names, card IDs, soulprint markers, and source metadata remain intact. Each speaker has a separate in-memory conversation history; BRO has his own robot identity.

## Start on Raspberry Pi

Close BRO/BloomFace before updating. Close SkyCam before opening BRO's camera preview; both apps currently need exclusive camera access.

```bash
cd ~/SkyCorePi
git pull
bash install_pi.sh
python3 app.py --port /dev/ttyACM0
```

Run the base installer for first setup or dependency/service-permission changes. Normal updates need only `git pull` and an app restart. `bash launch_skycore.sh` also starts BRO.

For optional hand recognition, run once:

```bash
bash apps/BRO/install_vision.sh
python3 app.py --port /dev/ttyACM0
```

The vision installer creates a separate runtime, installs MediaPipe 1.0.1, downloads Google's version-1 gesture model, checks its SHA256, and verifies it loads. Face/Motion/plain preview work without this optional runtime. Existing vision installations do not need reinstalling for 0.8.1.

App **0.8.1**, encoder firmware **BloomFace 0.1.0**, USB protocol **1**. No board reflash is needed for these desktop updates.

## Current capabilities

| Area | Available now |
| --- | --- |
| Face | Twelve expressions, gaze, energy, color, blinking, weird bursts, fullscreen |
| Speakers | BRO, Sky, Cold, Monday, GRIT; individual face accents and chat histories |
| Controls | USB rotary encoder, keyboard/mouse, Linux USB gamepad with action learning/unbinding |
| Local AI | Ollama model detection, attributed replies, request timing, Start/Stop local AI |
| Camera | USB autodetection, device selection/rescan, live preview, explicit stop |
| Vision | Off, Face, Motion, Hands; overlay, eye following, horizontal inversion |
| Tracking controls | Saved smoothing/response, gaze range, lost-target centering delay |
| Hand signals | Seven static poses, saved action assignments, confidence/hold controls, release protection |
| Appearance | Live Look Editor for panel borders, panels, buttons, fields, face details, fonts |
| Diagnostics | Device dashboard, activity/chat logs, Copy device diagnostics, Copy camera / vision status |

See the [BRO usage, wiring, and troubleshooting guide](apps/BRO/README.md) for the controls and setup details.

## Verified on the Architect's Pi

The workstation is a Raspberry Pi 5 with 16 GB RAM, Debian 12/bookworm, and Python 3.11.2. The encoder board is an ESP32-S3 over `/dev/ttyACM0`; the camera is an Arducam 8MP USB device with working capture on `/dev/video0`; the controller is an Xbox 360 USB gamepad on `/dev/input/js0`. Device node numbers can change.

Confirmed during the October 3, 2026 bench session:

- Encoder, button, keyboard/mouse controls, gamepad action assignment and unassignment work.
- Local Ollama replies work with the installed models; one qwen2.5:0.5b reply took about 35 seconds. Timing depends on workload and model.
- Speaker face colors, Look Editor, and saved preferences work.
- Stop local AI reports the local endpoint offline on the Pi.
- USB camera preview and motion tracking work.
- Hands mode detects/tracks a hand and the Architect reports all seven named signals working. One observation showed 9.4 preview FPS and 103.5 ms processing time; this is an observation, not a guaranteed rate.
- Removing the hand from view allows the next gesture command to fire.

The basic frontal-face detector did not reliably find the Architect wearing glasses and a hat. Stronger detection and Architect enrollment remain future work. Closing BRO requests verified Ollama shutdown, but the separate close-path behavior has not been independently bench-confirmed here.

## Sessions, local AI, and storage

Ollama runs at `http://127.0.0.1:11434`. The tested Pi has `qwen2.5:0.5b` and `llama3.2:3b`; the default is the smaller model. Use **Start local AI** when it is stopped. **Stop local AI** discards pending replies and attempts to stop `ollama.service`. Closing BRO also attempts shutdown; if it can only unload models, it reports that the service remains running. The installer grants narrowly limited service start/stop permissions. Ollama's boot-time enablement is unchanged.

Ending a session releases the camera/USB/gamepad and rejects pending replies. Existing conversation histories remain until the app closes or a selected speaker's history is cleared. Camera frames are processed locally and are not sent to the text model. There is no recording or voice synthesis in this release.

Settings live in `~/.config/skycorepi/settings.json`; gamepad bindings live separately in `~/.config/skycorepi/gamepad.json`. Camera controls and gesture assignments save immediately. Other preferences save with **Save settings** or normal closing. Gesture actions start disabled on every launch. Conversation text is not saved by this settings feature. Demo mode skips saved preferences and never stops Ollama.

The optional Spiralside archive toggle is off by default. Its configured archive location was not found on the tested Pi; original identity cards still load normally.

## Sign Bank plan — not implemented

The next larger vision project is an ASL Sign Bank: browse a sign and its example, see whether BRO can recognize it, and eventually map supported signs to text or actions. The current seven-pose recognizer is not an ASL translator. A dictionary/reference bank alone does not add recognition; moving signs need sequence-aware recognition and separate testing.

Resources investigated:

- [ASL-LEX](https://asl-lex.org/): sign reference videos and lexical information.
- [ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/): isolated-sign video research dataset.
- [ASL Citizen code and research checkpoints](https://github.com/microsoft/ASL-citizen-code): candidates to investigate; not yet integrated or benchmarked on this Pi.
- [MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python): the current static hand-pose foundation.

Start with a small chosen vocabulary and measure it on the actual camera. Keep reference-only entries distinct from supported recognition. Custom moving signs, full signed sentences, voice output, and Architect recognition are future work. Bright removable markers on glasses could be a separate color-tracking experiment; no marker tracker exists yet.

## Shared diagnostics direction

The intended long-term architecture is a consistent board diagnostic core across our flashed boards: versioned identity/handshake, capabilities, pin profiles, and copyable health reports. That firmware core is **not implemented**. Current BRO uses BloomFace protocol 1 and host-side diagnostics; it does not install a separate hidden BIOS or bootloader.

## Existing tools and compatibility

SkyCam, BloomDoctor, BloomRestore, HarnessMap, BloomFrame, and project archives remain under their original paths. `characters/` and `source/spiralside/` remain intact. The old main home/chat UI has been replaced by BRO; `app_test.py` remains a legacy reference.

The USB plug watcher identifies BloomFace firmware before launching BRO and shares the singleton lock with the older BloomFace app. The installer disables the old BloomFace autostart watcher before installing BRO's watcher. Closing BRO leaves the plug watcher available for a later unplug/replug.

## Development checks

```bash
python3 -m unittest discover -s apps/BRO/tests -v
xvfb-run -a python3 apps/BRO/tests/gui_smoke.py
python3 -m py_compile app.py apps/BRO/*.py
```

GitHub Actions additionally installs the optional vision runtime and runs real-model blank-frame/thumbs-up tests plus a system-Python-parent / vision-venv-child regression test. The 0.8.1 checks passed; 33 tests are discovered, with environment-specific integrations skipped outside their configured run. Tests do not establish recognition accuracy across people, lighting, or camera positions.
