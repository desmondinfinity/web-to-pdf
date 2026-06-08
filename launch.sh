#!/bin/bash
cd "$(dirname "$0")"
exec WAYLAND_DISPLAY=wayland-1 python3 main.py "$@"
