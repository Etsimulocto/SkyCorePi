# BloomFrame Studio

Raspberry Pi-native image frame maker for SkyCorePi.

## Features

- Load PNG, JPEG, WebP, BMP, and TIFF images
- Live Pi-friendly preview
- Four rotary knobs: brightness, contrast, color, sharpness
- Sliders for outer frame, inner frame, gap, mat, corners, bevel, rotation, scale, vignette, shadow, glow, and procedural texture
- Color pickers for every frame layer, glow, and shadow
- Textures: stripes, dots, crosshatch, noise, and wood
- Nine one-click presets
- Random frame generator
- Horizontal and vertical image flipping
- PNG, JPEG, and WebP export

## Install

```bash
sudo apt update
sudo apt install -y python3-pil python3-pil.imagetk python3-tk
```

Alternative Pillow install:

```bash
python3 -m pip install Pillow
```

## Run

```bash
cd ~/SkyCorePi/apps/BloomFrame
python3 bloomframe_studio.py
```

## Controls

The knobs respond to mouse-wheel movement or vertical click-and-drag. Sliders update the preview automatically. The source image remains unchanged until a new export file is selected.
