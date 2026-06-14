#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"

step() { echo; echo "── $1 ──"; }

echo "==================================="
echo "  Web to PDF — Installer"
echo "==================================="

# ── Python check ──────────────────────────────────────────────────────────────
step "Checking Python"
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is required."
    echo "  Linux : install via your package manager (e.g. sudo apt install python3)"
    echo "  macOS : brew install python  or  https://www.python.org"
    exit 1
fi
PY=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python $PY"

# ── System dependencies ────────────────────────────────────────────────────────
step "Installing system dependencies"

if [ "$OS" = "Linux" ]; then
    if command -v pacman &>/dev/null; then
        sudo pacman -S --needed --noconfirm python-pyqt6 poppler
    elif command -v apt-get &>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3-pip python3-pyqt6 poppler-utils
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pip python3-pyqt6 poppler-utils
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y python3-pip python3-qt6 poppler-tools
    else
        echo "WARNING: Unknown package manager — skipping system packages."
        echo "  Please ensure PyQt6 and poppler (pdfunite) are installed manually."
    fi

elif [ "$OS" = "Darwin" ]; then
    if ! command -v brew &>/dev/null; then
        echo "ERROR: Homebrew is required on macOS."
        echo "  Install from: https://brew.sh then re-run this script."
        exit 1
    fi
    brew install poppler
fi

# ── Python packages ────────────────────────────────────────────────────────────
step "Installing Python packages"
# Always use a venv to avoid conflicts with externally-managed system Python (PEP 668)
python3 -m venv --system-site-packages "${SCRIPT_DIR}/.venv"
VENV_PIP="${SCRIPT_DIR}/.venv/bin/pip"
VENV_PY="${SCRIPT_DIR}/.venv/bin/python"

if command -v pacman &>/dev/null; then
    # PyQt6 already installed system-wide via pacman; only need playwright
    "${VENV_PIP}" install --quiet playwright
else
    "${VENV_PIP}" install --quiet PyQt6 playwright
fi

step "Installing Playwright browser"
"${VENV_PY}" -m playwright install chromium

# ── Desktop entry (Linux only) ─────────────────────────────────────────────────
if [ "$OS" = "Linux" ]; then
    step "Creating desktop entry"
    ICON="/usr/share/icons/breeze-dark/mimetypes/64/application-pdf.svg"
    [ -f "$ICON" ] || ICON="application-pdf"
    mkdir -p ~/.local/share/applications
    cat > ~/.local/share/applications/web-to-pdf.desktop <<DESKTOP
[Desktop Entry]
Name=Web to PDF
Comment=Convert web pages to PDF, with D&D Beyond login support
Exec=${SCRIPT_DIR}/launch.sh
Icon=${ICON}
Terminal=false
Type=Application
Categories=Utility;Office;
Keywords=pdf;web;convert;url;html;dnd;dndbeyond;
StartupNotify=true
DESKTOP
    echo "Desktop entry written to ~/.local/share/applications/web-to-pdf.desktop"
fi

chmod +x "${SCRIPT_DIR}/launch.sh"

echo
echo "==================================="
echo "  Installation complete!"
echo "  Run the app: ./launch.sh"
[ "$OS" = "Linux" ] && echo "  Or launch from your application menu."
echo "==================================="
