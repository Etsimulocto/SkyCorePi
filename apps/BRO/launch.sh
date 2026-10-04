#!/usr/bin/env bash
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/.cache/bloomface/launch.log"
mkdir -p "$(dirname "$LOG")"

# If BRO is already alive, bring his existing window forward instead of
# silently exiting on the singleton lock.
if pgrep -f '[p]ython3 .*BRO/bloomface.py' >/dev/null 2>&1; then
  if command -v wmctrl >/dev/null 2>&1; then
    wmctrl -a 'BRO · BloomFace' >/dev/null 2>&1 || true
  fi
  exit 0
fi

cd "$HERE"
{
  echo "==== BRO launch $(date --iso-8601=seconds) ===="
  exec python3 "$HERE/bloomface.py" "$@"
} >>"$LOG" 2>&1
