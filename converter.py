from dataclasses import dataclass
import os
import subprocess
import tempfile
from playwright.sync_api import sync_playwright
from session import SESSION_FILE, DND_URL


@dataclass
class ConvertOptions:
    urls: list
    output_path: str
    format: str = "A4"
    landscape: bool = False
    margin_top: str = "1cm"
    margin_right: str = "1cm"
    margin_bottom: str = "1cm"
    margin_left: str = "1cm"
    print_background: bool = True
    wait_until: str = "networkidle"


_DND_CLEANUP_JS = """
    document.querySelectorAll('*').forEach(el => {
        const pos = getComputedStyle(el).position;
        if (pos === 'fixed' || pos === 'sticky') el.remove();
    });
    document.body.style.paddingTop = '0';
    document.body.style.marginTop = '0';
    const main = document.querySelector('main, #main, .main-content, [role="main"]');
    if (main) {
        main.style.paddingTop = '0';
        main.style.marginTop = '0';
    }
"""


def convert_to_pdf(options: ConvertOptions, progress_callback=None) -> None:
    def report(msg):
        if progress_callback:
            progress_callback(msg)

    urls = options.urls
    multi = len(urls) > 1
    has_dnd = any(DND_URL in u for u in urls)
    use_session = SESSION_FILE.exists() and has_dnd

    with sync_playwright() as p:
        report("Launching browser...")
        browser = p.chromium.launch(headless=True)

        if use_session:
            report("Loading D&D Beyond session...")
            context = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = browser.new_context()

        temp_files = []
        try:
            for i, url in enumerate(urls):
                prefix = f"[{i+1}/{len(urls)}] " if multi else ""
                report(f"{prefix}Loading {url}...")

                page = context.new_page()
                page.goto(url, wait_until=options.wait_until, timeout=60_000)

                if DND_URL in url:
                    report(f"{prefix}Cleaning up D&D Beyond UI...")
                    page.evaluate(_DND_CLEANUP_JS)

                if multi:
                    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                    tmp.close()
                    temp_files.append(tmp.name)
                    out_path = tmp.name
                    report(f"{prefix}Rendering...")
                else:
                    out_path = options.output_path
                    report("Rendering page...")

                page.pdf(
                    path=out_path,
                    format=options.format,
                    landscape=options.landscape,
                    margin={
                        "top": options.margin_top,
                        "right": options.margin_right,
                        "bottom": options.margin_bottom,
                        "left": options.margin_left,
                    },
                    print_background=options.print_background,
                )
                page.close()

            browser.close()

            if multi:
                report(f"Merging {len(urls)} PDFs...")
                subprocess.run(
                    ["pdfunite"] + temp_files + [options.output_path],
                    check=True, capture_output=True,
                )

        finally:
            for f in temp_files:
                try:
                    os.unlink(f)
                except OSError:
                    pass

    report(f"Saved to {options.output_path}")
