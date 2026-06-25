# BloomFrame Studio

Raspberry Pi-native image frame and panel maker for SkyCorePi.

## Apps

### `bloomframe_studio.py`

Single-image frame maker.

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

### `bloompanel_breaker.py`

Comic/collage/page slicer for turning one large multi-image picture into many framed exports.

- Load one large comic page, collage, screenshot sheet, or multi-image image
- Draw panel boxes manually with left-click drag
- Right-click a panel box to delete it
- Click a panel box to select it
- Auto Grid mode for fast rows/columns slicing
- Experimental Auto Detect mode for black-gutter comic pages
- Export one selected panel or all panels
- Each crop gets a wild frame automatically
- Export styles: Chaos Neon, Comic Ink, Polaroid Stack, Walnut Relic, Sky Glass, Science Snap, System Card, and Random Per Panel
- Controls for grid rows/columns, gutters, trim, detection threshold, minimum panel size, frame width, mat, radius, bevel, ink jitter, glow, shadow, texture, color boost, and frame colors

## Install

```bash
sudo apt update
sudo apt install -y python3-pil python3-pil.imagetk python3-tk
```

Windows / pip install:

```bash
python -m pip install Pillow
```

## Run: single image frame maker

```bash
cd ~/SkyCorePi/apps/BloomFrame
python3 bloomframe_studio.py
```

Windows:

```bash
cd ~/SkyCorePi/apps/BloomFrame
python bloomframe_studio.py
```

## Run: panel breaker

```bash
cd ~/SkyCorePi/apps/BloomFrame
python3 bloompanel_breaker.py
```

Windows:

```bash
cd ~/SkyCorePi/apps/BloomFrame
python bloompanel_breaker.py
```

## Panel Breaker controls

1. Load a big image.
2. Use `Auto Grid` for clean rows/columns, or drag boxes around panels manually.
3. Tune the frame controls or pick a preset.
4. Use `Export Selected` or `Export All`.

The source image is never overwritten. Exports are written as separate PNG files into the folder you choose.
