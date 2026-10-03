#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo apt-get install -y python3-tk python3-serial python3-opencv
bash "$HERE/apps/BRO/install_pi.sh"
