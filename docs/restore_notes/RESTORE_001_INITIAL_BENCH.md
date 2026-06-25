# Restore 001 — Initial Camera + Harness Bench

## Status

STABLE

## Working

- Raspberry Pi 5
- Arducam 8MP USB Camera
- SkyCam
- HarnessMap
- BloomRestore
- GitHub backup
- ILI9488 TFT LCD-only harness

## Known Issues

- Camera struggles with macro close-ups.
- 8BitDo controller not configured yet.
- Touch controller not wired yet.
- SkyCam must support both X11 and Wayland clipboard.

## Hardware

- Raspberry Pi 5
- Arducam 8MP USB Camera
- ILI9488 3.5 inch TFT SPI 480x320
- RJ45 harness
- USB switch

## Software Added

- SkyCam
- HarnessMap
- BloomRestore

## Files Added

- `apps/SkyCam`
- `apps/HarnessMap`
- `apps/BloomRestore`

## Things Changed

- Desktop launchers
- Autostart entries
- Camera clipboard utility
- Harness data file
- Restore-point utility

## Things NOT to Touch

- Working TFT harness
- Desktop launcher paths
- Restore point format
- GitHub backup flow

## Next Goal

- Make SkyCam auto-detect Arducam by name.
- Add Git status to BloomRestore.

## Lessons Learned

- Always meter RJ45 conductors.
- Bad ground causes haunted LCD.
- Never assume `/dev/video0`.
- Support X11 and Wayland.
- Create restore point before changing working code.

## Sky Notes

Known-good baseline for BloomCore bench utilities.
Return here if future app changes break camera, harness map, or desktop launchers.
