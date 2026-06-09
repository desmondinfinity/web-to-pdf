#!/bin/bash
cd "$(dirname "$0")"
export WAYLAND_DISPLAY=wayland-1
exec python3 main.py "$@"
