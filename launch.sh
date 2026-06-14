#!/usr/bin/env bash
cd "$(dirname "$0")"

# Auto-detect Wayland socket on Linux if not already set in the environment
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ "$(uname)" = "Linux" ]; then
    for _sock in /run/user/$(id -u)/wayland-*; do
        if [ -S "$_sock" ]; then
            export WAYLAND_DISPLAY="$(basename "$_sock")"
            break
        fi
    done
fi

if [ -f ".venv/bin/python" ]; then
    exec .venv/bin/python main.py "$@"
else
    exec python3 main.py "$@"
fi
