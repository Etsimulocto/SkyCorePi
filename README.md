# SkyCorePi / BRO 0.7.1

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

Tests: `python3 -m unittest discover -s apps/BRO/tests -v`; UI: `xvfb-run -a python3 apps/BRO/tests/gui_smoke.py`. Real local inference still needs verification on the Pi. App 0.7.1, board firmware 0.1.0, USB protocol 1.

## Conversation feedback (0.4.1)

The face shows IDLE, THINKING, REPLYING or ERROR. Thinking has bouncing mouth dots; REPLYING briefly animates the mouth after text arrives (no audio/TTS). Speaker context explicitly distinguishes the selected speaker from the Architect. Model behavior still needs testing. **Clear selected speaker chat** clears only that speaker history and displayed lines, and discards a pending reply for that speaker. Other speaker histories remain. Diagnostics include selected model/speaker, local endpoint, last request model/speaker, elapsed time and errors.

## Speaker face colors (0.4.2)

Selecting a speaker changes the face accent: BRO mint/teal, Sky blue, Cold ice cyan, Monday pink, GRIT amber. COLOR knob adjustments are remembered per speaker for the current app run. Names and source identity cards remain unchanged.

## Gamepad (0.5.0)

Pi/Linux controllers exposed as `/dev/input/js*` autodetect and reconnect. Default typical Xbox mapping: left stick horizontal looks left/right, button0 next control, button1 weird burst, button4/5 previous/next speaker. Numbering varies: use **Learn next button / direction** to assign any observed button or axis direction to a named action. Select an action, learn, then press a button or move a centered stick. Learning consumes the input without triggering its action, times out after 15 seconds, and can be cancelled. Assign **None** to unbind an input. Show bindings copies them into the normal log. Restore defaults resets saved assignments.

Bindings save locally to `~/.config/skycorepi/gamepad.json` across restarts. A single mapping is used for the selected controller; select a device when several are attached. Dead zone and direction latching avoid repeated actions while held. Return a stick to center before another step. Gaze stays where assigned; map Center gaze to a button if desired. Session end closes gamepad input. No rumble or motors are driven. Windows gamepad support remains future work.

If USB appears in lsusb but no joystick node appears, run `ls /dev/input/js*` and check the joydev driver/desktop input permissions; do not run BRO as root. Real Xbox button numbering still needs bench validation.

## Saved settings and device dashboard (0.5.1)

The Devices / settings panel reports session, USB, gamepad, camera and Ollama status, with reconnect/detect buttons and Copy device diagnostics. Ollama status reflects the latest model check or chat result; Check Ollama refreshes it. Saved preferences include model, speaker, per-speaker hues, camera/gamepad selections, serial port, knob direction/edges and window geometry. Save settings explicitly or close normally to save to `~/.config/skycorepi/settings.json`. Demo mode does not read or write preferences. Camera capture is started through the preview controls, not automatically by restoring its selection. Gamepad bindings remain in their separate settings file. CLI --port overrides the saved port. Conversation text is not stored by this feature.

## Local AI power (0.5.2)

Run `bash install_pi.sh` once for this update. It installs a sudoers rule limited to starting/stopping `ollama.service` for your user; it validates the rule before installation. **Stop local AI** discards pending chat replies and stops Ollama. **Start local AI** restarts it for conversation. Closing BRO also attempts verified Ollama shutdown, printing the result in the terminal and saving `~/.cache/skycorepi/ai-shutdown.txt`. If service control is unavailable, loaded models are unloaded and the report explicitly says the service remains running. Shared Ollama clients are also interrupted when the service stops. Demo mode never stops Ollama. This feature does not disable Ollama's boot-time service enablement.

## Look Editor (0.6.0)

Top header **Look Editor** opens live theme controls: background, panels, header, text, buttons/hover/text, fields, face background, grid/scan line, eye shadows/pupils/highlights and cheeks. Pick a color for immediate preview or enter six-digit hex values and Apply. Choose installed UI, text and face fonts; UI/text sizes range from 8–24. Save persists the look with settings; normal app closing also saves the current look. Reset look restores the default theme. Speaker eye accents retain their per-speaker colors and COLOR knob adjustments. No identity cards change.

Look Editor 0.6.1 replaces the obscured root Background control with **Panel Border**, visibly coloring framed panel outlines and text-box borders. Existing saved Background values migrate to Panel Border.

## Vision tracking (0.7.0)

Install this update with `bash install_pi.sh` to include OpenCV face cascade data. Enable Camera preview, then choose **Face** or **Motion** below its controls. Face uses a frontal-face Haar detector; Motion uses background differences for a stationary camera. A box and target crosshair show observations; the largest initial target is selected, then the closest target center. This is basic target continuity, not identity recognition. Face detection may miss profiles, small faces or poor lighting.

**Eyes follow target** smoothly controls pupils in both axes. On losing a target, gaze holds briefly then centers. Manual gaze inputs can compete with tracking; disable Eyes follow target to use manual gaze. Some stylized expressions override horizontal pupil position. **Tracking overlay** hides/shows marks. Vision off keeps plain preview. Frame capture remains shared with preview in its existing child process; detection runs about five times a second on reduced frames. Diagnostics show searching/tracking, target count and detection time; only state transitions are logged. Camera stops on hide/session end/app close. No recording, identification, cloud inference, chat image input or motor commands are added. Object/hand/marker modes remain later additions. Real Pi camera tracking needs testing.

Camera direction (0.7.1): **Invert gaze X (left / right)** reverses only camera-driven horizontal eye movement. It starts enabled for a camera facing you. Toggle it while moving left/right to match your setup; the choice saves immediately and loads next launch. The preview and tracking overlay retain the original camera orientation.
