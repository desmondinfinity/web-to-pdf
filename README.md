# Web to PDF

![CI](https://github.com/desmondinfinity/web-to-pdf/actions/workflows/ci.yml/badge.svg)

A desktop app that converts web pages to PDF files. Supports combining multiple pages into a single PDF (useful for saving a book that spans multiple chapters across different URLs), and includes a D&D Beyond login flow so you can save protected campaign and character pages.

---

## Features

- Convert any web page to a PDF in one click
- **Multi-chapter support** — paste multiple URLs (one per line) and they are merged into a single PDF in order
- D&D Beyond login — saves your session so protected pages render correctly
- Page format, orientation, margins, and background options
- Dark-themed desktop GUI (PyQt6)

---

## Requirements

- **Python 3.9 or newer**
- **Git** (to clone the repo)
- **Opera GX** — required only if you want D&D Beyond login support

---

## Installation

### Linux

**1. Clone the repository**

```bash
git clone https://github.com/desmondinfinity/web-to-pdf.git
cd web-to-pdf
```

**2. Run the install script**

```bash
bash install.sh
```

The script automatically detects your package manager and installs all dependencies:

| Distro | Package manager used |
|---|---|
| Arch / CachyOS / Manjaro | `pacman` |
| Ubuntu / Debian / Mint | `apt` |
| Fedora / RHEL / CentOS | `dnf` |
| openSUSE | `zypper` |

It also installs the Playwright Chromium browser used for rendering and creates a desktop entry so the app appears in your application launcher.

**3. Launch the app**

```bash
./launch.sh
```

Or search for **Web to PDF** in your application menu.

---

### macOS

**1. Install Homebrew** (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Clone the repository**

```bash
git clone https://github.com/desmondinfinity/web-to-pdf.git
cd web-to-pdf
```

**3. Run the install script**

```bash
bash install.sh
```

This installs `poppler` (for multi-chapter merging) via Homebrew, then installs the Python packages and Playwright Chromium browser.

**4. Launch the app**

```bash
./launch.sh
```

---

### Windows

**1. Install Python 3.9+**

Download and run the installer from [python.org](https://www.python.org/downloads/).

> **Important:** On the first screen of the installer, check **"Add Python to PATH"** before clicking Install.

**2. Clone the repository**

Open **PowerShell** or **Command Prompt** and run:

```powershell
git clone https://github.com/desmondinfinity/web-to-pdf.git
cd web-to-pdf
```

If you don't have Git, download it from [git-scm.com](https://git-scm.com/download/win).

**3. Run the install script**

In PowerShell (run as a normal user, not Administrator):

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

This installs PyQt6, Playwright, the Chromium browser, and automatically downloads the poppler tools (including `pdfunite`) needed for multi-chapter merging.

**4. Launch the app**

Double-click `launch.bat`, or from the terminal:

```powershell
launch.bat
```

---

## Using the App

### Converting a single web page

1. Paste the URL into the **Web Page URLs** box
2. Set an output file path with **Browse...**
3. Adjust any options (page size, margins, etc.)
4. Click **Convert to PDF**

### Combining multiple pages into one PDF

Paste each URL on its own line in the URL box — they become chapters in the output PDF, merged in order:

```
https://example.com/chapter-1
https://example.com/chapter-2
https://example.com/chapter-3
```

The app renders each page separately and then merges them automatically.

### D&D Beyond login

Some D&D Beyond pages (campaigns, full adventures) require you to be logged in:

1. Click **Login...** in the D&D Beyond section
2. Opera GX will open and navigate to the D&D Beyond login page
3. Log in with your D&D Beyond account as you normally would
4. Once logged in, click **Done — Save Session** in the app
5. Your session is saved locally and will be used automatically for future conversions

To log out and clear the saved session, click **Logout**.

> **Note:** The D&D Beyond login flow uses Opera GX because it bypasses detection that blocks headless browsers. Opera GX must be installed for this feature to work.

---

## Options

| Option | Description |
|---|---|
| **Page format** | Paper size: A4, A3, A5, Letter, Legal, Tabloid |
| **Landscape** | Switch to horizontal orientation |
| **Background colors & images** | Include CSS backgrounds in the PDF (recommended: on) |
| **Margins** | None, Small (0.5cm), Normal (1cm), Large (2cm) |
| **Wait until** | When to consider the page loaded — `networkidle` waits for all network activity to stop (recommended for complex pages); `load` and `domcontentloaded` are faster but may miss late-loading content |

---

## Troubleshooting

**The app won't start after install**

Make sure `launch.sh` is executable:
```bash
chmod +x launch.sh
```

**D&D Beyond pages don't load correctly / show a login wall**

Your session may have expired. Click **Logout** in the app, then **Login...** again to save a fresh session.

**D&D Beyond login button does nothing (non-Linux systems)**

The login flow opens Opera GX using its default Linux path (`/usr/bin/opera-gx`). On macOS or Windows you may need to edit `session.py` and update `executable_path` to point to your Opera GX installation:

- macOS: `/Applications/Opera GX.app/Contents/MacOS/Opera`
- Windows: `C:\Users\<you>\AppData\Local\Programs\Opera GX\opera.exe`

**Multi-chapter merge fails**

Ensure `pdfunite` is installed:
- Linux: `pdfunite --version` — if missing, install `poppler-utils` via your package manager
- macOS: `brew install poppler`
- Windows: re-run `install.ps1` — it downloads pdfunite automatically into the `bin/` folder

**Pages render with missing content or cut off**

Try changing **Wait until** from `networkidle` to `load`, or increase the page timeout by using a simpler page that doesn't rely on heavy JavaScript.
