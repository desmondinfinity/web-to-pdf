from dataclasses import dataclass
from pathlib import Path
from playwright.sync_api import sync_playwright
from session import SESSION_FILE, DND_URL


@dataclass
class ConvertOptions:
    url: str
    output_path: str
    format: str = "A4"
    landscape: bool = False
    margin_top: str = "1cm"
    margin_right: str = "1cm"
    margin_bottom: str = "1cm"
    margin_left: str = "1cm"
    print_background: bool = True
    wait_until: str = "networkidle"


def convert_to_pdf(options: ConvertOptions, progress_callback=None) -> None:
    def report(msg):
        if progress_callback:
            progress_callback(msg)

    use_session = SESSION_FILE.exists() and DND_URL in options.url

    with sync_playwright() as p:
        report("Launching browser...")
        browser = p.chromium.launch(headless=True)

        if use_session:
            report("Loading D&D Beyond session...")
            context = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = browser.new_context()

        page = context.new_page()

        report(f"Loading {options.url}...")
        page.goto(options.url, wait_until=options.wait_until, timeout=60_000)

        if DND_URL in options.url:
            report("Cleaning up D&D Beyond UI...")
            page.evaluate("""
                // Remove all fixed/sticky elements (nav bar, promo banners)
                document.querySelectorAll('*').forEach(el => {
                    const pos = getComputedStyle(el).position;
                    if (pos === 'fixed' || pos === 'sticky') {
                        el.remove();
                    }
                });
                // Undo any top padding/margin the page added to compensate for fixed header
                document.body.style.paddingTop = '0';
                document.body.style.marginTop = '0';
                const main = document.querySelector('main, #main, .main-content, [role="main"]');
                if (main) {
                    main.style.paddingTop = '0';
                    main.style.marginTop = '0';
                }
            """)

        report("Rendering page...")
        page.pdf(
            path=options.output_path,
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

        browser.close()
        report(f"Saved to {options.output_path}")
