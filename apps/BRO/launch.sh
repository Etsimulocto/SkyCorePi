#!/usr/bin/env bash
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/.cache/bloomface/launch.log"
mkdir -p "$(dirname "$LOG")"
cd "$HERE"
{
  echo "==== BRO launch $(date --iso-8601=seconds) ===="
  exec python3 "$HERE/bloomface.py" "$@"
} >>"$LOG" 2>&1
