#!/bin/bash
# install_desktop_launchers.sh
# run with: bash ~/SkyCorePi/scripts/install_desktop_launchers.sh
# path: /home/quarterbitgames/SkyCorePi/scripts/install_desktop_launchers.sh
# description: Restores BloomCore desktop launchers from the SkyCorePi repo.
# version: 1.0
# format: bloomcore/v1.3

set -e

REPO="$HOME/SkyCorePi"
SRC="$REPO/desktop_launchers"
DESKTOP="$HOME/Desktop"
APPS="$HOME/.local/share/applications"

mkdir -p "$DESKTOP" "$APPS"

for file in SkyCam.desktop HarnessMap.desktop BloomRestore.desktop BloomDoctor.desktop; do
    if [ -f "$SRC/$file" ]; then
        cp "$SRC/$file" "$DESKTOP/$file"
        cp "$SRC/$file" "$APPS/$file"
        chmod +x "$DESKTOP/$file" "$APPS/$file"
        echo "Installed $file"
    else
        echo "Missing $SRC/$file"
    fi
done

echo "BloomCore desktop launchers restored."
