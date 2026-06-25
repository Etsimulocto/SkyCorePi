# Sky Engineering Notes

## Current Purpose

SkyCorePi is the Raspberry Pi bench environment for BloomCore hardware/software experiments.

## Recovery Priority

1. Restore SkyCam
2. Restore HarnessMap
3. Restore BloomRestore
4. Verify camera
5. Verify TFT
6. Push stable changes to GitHub

## Current Risk Areas

- X11 vs Wayland clipboard tools
- USB switch disconnecting camera
- Hardcoded `/dev/video0`
- Autostart duplicates
- Restore folders growing large

## Desired Pattern

Every app should:

- Have BloomCore header
- Be simple to run
- Have desktop icon
- Be recoverable
- Save plain-text or JSON data
- Avoid hidden dependencies
