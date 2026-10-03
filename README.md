# SkyCorePi / BRO 0.4.1

BRO's robot development console: animated face, USB rotary controls, local Ollama chat, camera preview, speech and activity logs, and session controls. Sky, Cold, Monday and GRIT load their original identity cards from `characters/` without modifying them. Each speaker has a separate in-memory conversation history; BRO has his own new robot identity.

## Raspberry Pi

Close BloomFace and SkyCam before starting. Existing BloomFace firmware 0.1.0 and GPIO7/8/9 encoder wiring remain compatible; no reflash required.

```bash
cd ~/SkyCorePi
git pull
bash install_pi.sh
python3 app.py --port /dev/ttyACM0
```

The installer pauses the old BloomFace plug watcher and starts BRO's watcher, which identifies the firmware before launching. App singleton lock is shared with BloomFace to prevent duplicate windows. `bash launch_skycore.sh` also launches BRO. The former home/chat UI in `app.py` is replaced; `app_test.py` remains a legacy reference, not the launcher.

## Local conversation

Ollama must be running locally. **Detect models / diagnostics** loads installed models and appends host diagnostics to the copyable log. Select a model and speaker, enter a message in **Local conversation**, and send. The tested Pi has qwen2.5:0.5b and llama3.2:3b; default is qwen2.5:0.5b. Replies are attributed to the speaker captured when sending, even if selection changes. The camera is a preview only; frames are not sent to the text model. Messages go only to local Ollama, not a cloud service.

Optional **Use local Spiralside archive** uses the existing archive search at its configured path. It is off by default. The original card IDs and metadata remain untouched. There is no model training or identity-card rewrite. Histories are bounded and stay in memory; ending a session discards pending replies and releases camera/USB. Histories remain during the current app run; closing clears them.

Manual text tests remain explicitly labeled. Camera preview, USB reconnect, mouse/keyboard, knob controls and Copy log retain their existing behavior. Joystick support and a common firmware diagnostic core remain future work; host diagnostics explicitly report that core as not implemented.

## Existing bench tools

SkyCam, BloomDoctor, BloomRestore, HarnessMap, BloomFrame and project archives remain available under their original paths. SkyCam and BRO presently require exclusive camera ownership. Original `characters/` and `source/spiralside/` identity archives remain intact.

Tests: `python3 -m unittest discover -s apps/BRO/tests -v`; UI: `xvfb-run -a python3 apps/BRO/tests/gui_smoke.py`. Real local inference still needs verification on the Pi. App 0.4.1, board firmware 0.1.0, USB protocol 1.

## Conversation feedback (0.4.1)

The face shows IDLE, THINKING, REPLYING or ERROR. Thinking has bouncing mouth dots; REPLYING briefly animates the mouth after text arrives (no audio/TTS). Speaker context explicitly distinguishes the selected speaker from the Architect. Model behavior still needs testing. **Clear selected speaker chat** clears only that speaker history and displayed lines, and discards a pending reply for that speaker. Other speaker histories remain. Diagnostics include selected model/speaker, local endpoint, last request model/speaker, elapsed time and errors.
