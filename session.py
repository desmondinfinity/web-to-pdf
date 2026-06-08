import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_DIR = Path.home() / ".local/share/web-to-pdf"
SESSION_FILE = SESSION_DIR / "dnd_session.json"
DND_URL = "https://www.dndbeyond.com"


def is_logged_in() -> bool:
    return SESSION_FILE.exists()


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def run_login_browser(stop_event: threading.Event, on_done):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DISPLAY", ":1")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                executable_path="/usr/bin/opera-gx",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1280,800",
                    "--no-first-run",
                ],
                ignore_default_args=["--enable-automation"],
            )
            context = browser.new_context(
                no_viewport=True,
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/131.0.0.0"
                ),
            )

            # Hide the webdriver property so Google doesn't flag the browser
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            page = context.new_page()
            page.goto(f"{DND_URL}/login", wait_until="domcontentloaded", timeout=30_000)

            while not stop_event.is_set():
                try:
                    _ = page.url
                except Exception:
                    break
                stop_event.wait(timeout=0.5)

            try:
                context.storage_state(path=str(SESSION_FILE))
                saved = True
            except Exception as e:
                saved = False
                on_done(False, f"Could not save session: {e}")
                return
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

            on_done(saved, "Logged in to D&D Beyond." if saved else "Session not saved.")

    except Exception as e:
        on_done(False, str(e))
