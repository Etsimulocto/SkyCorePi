#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo apt-get install -y python3-tk python3-serial python3-opencv
if [[ -f "$HOME/.config/autostart/bloomface-plug-watch.desktop" ]]; then
  mv "$HOME/.config/autostart/bloomface-plug-watch.desktop" "$HOME/.config/autostart/bloomface-plug-watch.desktop.disabled"
fi
mkdir -p "$HOME/.local/share/applications" "$HOME/.config/autostart" "$HOME/.cache/bloomface"
cat > "$HOME/.local/share/applications/bloomface.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SkyCorePi BRO
Comment=A weird robot face with a USB rotary remote
Exec=python3 "$HERE/bloomface.py"
Path=$HERE
Icon=face-smile
Terminal=false
Categories=Development;Education;
EOF
if [[ -d "$HOME/Desktop" ]]; then
  cp "$HOME/.local/share/applications/bloomface.desktop" "$HOME/Desktop/BRO.desktop"
  chmod +x "$HOME/Desktop/BRO.desktop"
fi
cat > "$HOME/.config/autostart/bloomface-plug-watch.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SkyCorePi BRO USB Watcher
Exec=python3 "$HERE/plug_watch.py"
Path=$HERE
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
pkill -f '[p]ython3 .*BloomFace/plug_watch.py' 2>/dev/null || true
pkill -f '[p]ython3 .*BRO/plug_watch.py' 2>/dev/null || true
nohup python3 "$HERE/plug_watch.py" >> "$HOME/.cache/bloomface/watcher.log" 2>&1 < /dev/null &
echo 'BRO installed; its watcher will auto-open BRO firmware boards.'
