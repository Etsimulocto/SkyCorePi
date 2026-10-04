# BRO Video Effects

## Status

Implemented in `apps/BRO/camera.py` on October 4, 2026.

BRO now has local, display-only camera effects:

- Raw
- Soft
- Cartoon
- Ink
- Silhouette
- Pixel

An Effect strength slider changes the amount of processing. Effects can be changed live while the camera is running.

## BloomCore boundary

The camera pipeline intentionally separates machine vision from presentation:

```text
CAMERA
  |
  +--> RAW FRAME --> Face / Motion / Hands tracking
  |
  +--> PREVIEW COPY --> selected video effect --> BRO camera preview
```

Do not move the effect stage ahead of tracking casually. Cartoon, silhouette, edge and pixel filters remove information that MediaPipe/OpenCV tracking may need.

This means video effects are useful for presentation and privacy without silently destabilizing the known-good tracking layer.

## Privacy notes

`Silhouette`, `Ink`, and especially `Pixel` reduce visible personal detail in the local preview. They are visual obfuscation tools, not anonymity guarantees. BRO still receives the raw camera frame locally for tracking when vision is enabled.

Camera frames remain local. This feature does not add recording, network streaming, or automatic upload.

## Background removal

True foreground/background segmentation is deliberately not claimed by this first version. A future `Flat BG` or `Blur BG` mode should use a tested segmentation model and remain a separate presentation layer unless bench testing proves a processed tracking input is better.

## Performance

Effects are implemented with OpenCV operations already available to BRO. `Raw`, `Ink`, `Silhouette`, and `Pixel` are relatively inexpensive. `Soft` and `Cartoon` use bilateral filtering and may reduce preview frame rate on the Raspberry Pi. If tracking responsiveness changes, compare against Raw before changing the vision subsystem.
