#!/usr/bin/env bash
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/.cache/bloomface/launch.log"
mkdir -p "$(dirname "$LOG")"

raise_bro() {
  command -v wmctrl >/dev/null 2>&1 || return 1
  if wmctrl -a 'SkyCorePi BRO' >/dev/null 2>&1; then
    return 0
  fi
  if wmctrl -a 'BRO · BloomFace' >/dev/null 2>&1; then
    wmctrl -r 'BRO · BloomFace' -T 'SkyCorePi BRO' >/dev/null 2>&1 || true
    return 0
  fi
  return 1
}

# If BRO is already alive, bring his existing window forward instead of
# silently exiting on the singleton lock.
if pgrep -f '[p]ython3 .*BRO/bloomface.py' >/dev/null 2>&1; then
  raise_bro || true
  exit 0
fi

cd "$HERE"
{
  echo "==== SkyCorePi BRO launch $(date --iso-8601=seconds) ===="
  python3 "$HERE/bloomface.py" "$@" &
  BRO_PID=$!

  # bloomface.py is still the internal firmware-facing module name. Rename
  # the desktop window to the actual application name once Tk creates it.
  if command -v wmctrl >/dev/null 2>&1; then
    for _ in $(seq 1 30); do
      if wmctrl -r 'BRO · BloomFace' -T 'SkyCorePi BRO' >/dev/null 2>&1; then
        break
      fi
      sleep 0.1
    done
  fi

  wait "$BRO_PID"
} >>"$LOG" 2>&1
