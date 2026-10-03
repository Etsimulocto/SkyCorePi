# BRO 0.8.1 — interface and bench guide

BRO's native Tk desktop app is the active robot interface in SkyCorePi. See the [repository README](../../README.md) for installation, bench results, the Sign Bank plan, and existing tools.

## Board and encoder wiring

Firmware is **BloomFace 0.1.0**, protocol **1**, on the ESP32-S3. Use GPIO labels on the board, not physical header positions.

| Encoder label | ESP32-S3 connection |
| --- | --- |
| GND | GND |
| + | 3V3 |
| CLK | GPIO7 |
| DT | GPIO8 |
| SW | GPIO9 |

The confirmed setup uses two encoder edges per detent. Select 2/4 edges and reverse direction in the app if your module differs. A tap changes the control; a hold of roughly 0.7 seconds produces a weird burst. Desktop updates do not require reflashing this compatible firmware. Firmware and `flash.sh` remain in this directory for board setup.

## Face and characters

The knob's control modes are **EXPRESSION**, **GAZE**, **ENERGY**, and **COLOR**. Expressions: CURIOUS, SIDE EYE, JOY, SLEEPY, PANIC, GREMLIN, VOID, LOVESTRUCK, STUBBORN, MELTING, DISCO, and SUSPICIOUS. Some stylized expressions deliberately override horizontal pupil position.

| Speaker | Default face accent |
| --- | --- |
| BRO | Mint / teal |
| Sky | Blue |
| Cold | Ice cyan |
| Monday | Pink |
| GRIT | Amber |

COLOR adjustments belong to the selected speaker. Saved preferences restore them. Source identity cards are not rewritten.

The top-header **Look Editor** previews colors and fonts. **Panel Border** changes panel outlines and text-box borders; old Background settings migrate to it. Other controls cover panels/header/text, buttons/hover, fields, face background/grid/scan lines, eye shadows/pupils/highlights, and cheeks. Choose installed fonts and UI/text sizes from 8–24. Save or close the app normally to persist the look.

## Gamepad and other inputs

Linux controllers exposed as `/dev/input/js*` autodetect and reconnect. The Xbox 360 controller and assignment workflow are bench-confirmed. Numbering varies between devices.

Select an action, click **Learn next button / direction**, then press a button or move a centered stick. Learning consumes the input without firing the action, expires after 15 seconds, and can be cancelled. Assign **None** to unbind. **Show bindings in log** reports assignments; **Restore defaults** resets them.

Default assignments are axis0 left/right → Look left/right, button0 → Next control, button1 → Weird burst, and button4/5 → Previous/Next speaker. Held axes do not repeat; return to center before another step. One saved mapping applies to the selected controller; per-controller profiles and Windows gamepad support remain future work. The adapter sends no rumble or motor commands.

Keyboard/mouse and rotary controls remain usable alongside the gamepad. Typing in text fields does not trigger global face controls. Disable camera **Eyes follow target** when testing manually assigned gaze actions to avoid the tracker overwriting them.

## Local conversation and text output

Select the speaker and model, enter a message in **Local conversation**, and send. Replies retain the speaker selected at send time even if you switch afterward. Each speaker has a separate bounded, in-memory history. **Clear selected speaker chat** clears only that speaker and cancels a pending reply for that speaker.

The face shows **IDLE**, **THINKING**, **REPLYING**, or **ERROR**. Reply mouth animation is visual feedback, not audio. Manual/sample text is labeled distinctly. Text output and activity logs are copyable; request diagnostics include the endpoint, speaker/model, elapsed time, and errors.

Use **Start local AI** / **Stop local AI** in the device panel. The latter stops the service when permitted; fallback model unloading is explicitly reported. Closing the app requests shutdown and writes the result to `~/.cache/skycorepi/ai-shutdown.txt`. Ending a session cancels interaction and releases devices; it is separate from stopping Ollama or closing the app.

## Camera and tracking

Enable Camera preview to open a device. Auto tries readable `/dev/video*` nodes; explicit selection and **Detect / rescan** are available. `/dev/video0` works for the tested Arducam. Other nodes may be metadata or Pi codec devices. Close SkyCam or other capture apps first.

| Mode | Behavior |
| --- | --- |
| Off | Plain live preview |
| Face | Basic frontal-face Haar detection; not identity recognition |
| Motion | Background-difference targets; keep the camera stationary |
| Hands | MediaPipe hand landmarks and the seven supported static signals |

Overlay boxes/marks show targets. Tracking selects the largest initial target, then the closest center; it cannot guarantee the same person's identity. **Eyes follow target** drives both gaze axes. On losing a target, gaze waits for the configured delay then centers.

**Invert gaze X (left / right)** reverses camera-driven horizontal gaze only. Compare directions while moving to choose what matches the camera placement. It does not mirror the preview. Response controls smoothing, range limits eye movement, and center delay controls how long lost-target gaze holds. Mode, overlay, following, inversion, and these controls save immediately and restore next launch. Restoring settings does not automatically open the camera.

Status reports target count, processing milliseconds, delivered preview FPS, and searching/tracking/errors. Detection runs about five times per second on reduced frames; preview FPS includes capture/processing overhead. The Architect observed 9.4 FPS / 103.5 ms once in Hands mode. It is not a fixed performance promise.

Use **Copy camera / vision status** beside the camera status, or **Copy device diagnostics** for the broader report including gesture bindings. Camera capture runs in a stoppable child process and stops when hidden, when the session ends, or when the app closes.

## Hand signal bank and assignment

Install with `bash apps/BRO/install_vision.sh` from the repository root, then restart BRO and select **Hands**. The optional environment is `~/.local/share/skycorepi/vision-venv`; the model is `~/.cache/skycorepi/gesture_recognizer.task`.

| Recognizer label | Pose |
| --- | --- |
| Open_Palm | Open hand / palm |
| Closed_Fist | Closed fist |
| Thumb_Up | Thumbs up |
| Thumb_Down | Thumbs down |
| Victory | Two-finger peace sign |
| Pointing_Up | Index finger pointing up |
| ILoveYou | Thumb, index, and little finger extended |

Choose a signal and action, click **Assign signal → action**, then enable **gesture actions**. Assignments, confidence, and hold duration save immediately. All signals initially map to **None**; actions start disabled on each launch. **None** unassigns an action.

Actions use the same vocabulary as the gamepad: gaze left/right/center, turn left/right, next control, weird burst, previous/next speaker, toggle camera, fullscreen, and clear selected speaker chat.

Hold a clear signal above the confidence threshold for the configured time. After firing, remove/lower the hand so recognition sees no valid signal for at least 0.4 seconds before another command. Switching directly to another recognized pose does not re-arm. Stalled frames do not count toward a hold or release. The Architect reports all seven signs working on the Pi, with taking the hand off-screen providing a reliable release.

**“None · 90%”** means the classifier selected its no-named-gesture category; it does not mean a supported sign was recognized with 90% confidence. Hand tracking can still report a target. A wave and left/right pointing are not supported classes. This is a small static gesture bank, not a full sign-language translator.

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| Hands unavailable: no module named mediapipe after a successful install | Update to 0.8.1 and restart. It fixes multiprocessing replacing the worker's vision package path. No reinstall is needed for that bug. |
| Vision runtime/model has never been installed | Run `bash apps/BRO/install_vision.sh`; wait for “MediaPipe ready.” Copy any failure output. |
| Hand detected but label is None | Try a distinct supported pose, held steady and clearly visible. Check confidence and hold duration. |
| Signal recognized but no command | Enable gesture actions, assign an action, hold it, then take the hand out of view before repeating. |
| Eye movement runs opposite your motion | Toggle Invert gaze X and compare. |
| Manual gaze gets overridden | Disable Eyes follow target. |
| Camera unreadable or busy | Close SkyCam/other camera apps, then rescan or select the capture node. |
| Face misses hat/glasses | This basic detector was unreliable for the Architect's usual appearance. Motion/Hands work independently; improved detection/enrollment is planned. |
| Ollama connection refused | Use Start local AI, then Check Ollama. Hand recognition does not require Ollama. |
| Archive not found | Leave the optional archive toggle off until the configured location is corrected. Identity cards still load. |
| USB handshake fails | Close competing serial apps, confirm the port and BloomFace firmware, then reconnect USB. |

Model-load warnings did not prevent the tested Pi installer from reporting ready. Actual errors are exposed in camera status and logs; copy them rather than assuming every warning is harmless.

## Future work

See the root [Sign Bank plan](../../README.md#sign-bank-plan--not-implemented). Reference videos/dictionaries, recognition models, and action assignments are distinct pieces. ASL-LEX and ASL Citizen are research/reference candidates, not installed features. Moving signs and signed sentences need sequence-aware models and testing. Architect enrollment, color-marker tracking for glasses, voice output, and the shared board diagnostic core are also unimplemented.
