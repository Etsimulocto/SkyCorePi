#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo apt-get install -y python3-tk python3-serial python3-opencv opencv-data
bash "$HERE/apps/BRO/install_pi.sh"

# Permit only starting/stopping this one service, without a desktop password prompt.
SYSTEMCTL_PATH="$(command -v systemctl)"
RULE_FILE="$(mktemp)"
printf '%s ALL=(root) NOPASSWD: %s start ollama.service, %s stop ollama.service\n' "$(id -un)" "$SYSTEMCTL_PATH" "$SYSTEMCTL_PATH" > "$RULE_FILE"
sudo visudo -cf "$RULE_FILE"
sudo install -o root -g root -m 0440 "$RULE_FILE" /etc/sudoers.d/skycorepi-ollama
