# Usage: python makepdf_sync.py input.html output.pdf
import sys, pathlib
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

WIDTH = "1920px"
HEIGHT = "1080px"

def run(input_html: str, output_pdf: str):
    in_path = pathlib.Path(input_html).resolve()
    if not in_path.exists():
        print(f"Input HTML not found: {input_html}")
        raise SystemExit(1)
    url = in_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080, "deviceScaleFactor": 1}
        )

        page.goto(url, wait_until="networkidle")

        # Ensure full-bleed and no accidental scaling in print
        page.add_style_tag(content=f"""
          @media print {{
            html, body {{ margin:0; padding:0; width:{WIDTH}; height:{HEIGHT}; }}
            .slide {{ width:{WIDTH} !important; height:{HEIGHT} !important;
                      break-after: page; transform:none !important; }}
          }}
          /* Chart canvas sizing (also applies in screen) */
            .chart-wrap canvas {{ width:100% !important; height:100% !important; display:block; }}
        """)

        # Wait for any charts and nudge a resize
        try:
            page.wait_for_selector("canvas", state="attached", timeout=5000)
        except PWTimeout:
            pass
        try:
            page.wait_for_function("() => window.Chart !== undefined", timeout=3000)
            page.evaluate("() => window.dispatchEvent(new Event('resize'))")
        except PWTimeout:
            pass

        page.wait_for_timeout(200)
        page.emulate_media(media="print")

        # CRITICAL: set explicit PDF page size and margins here
        page.pdf(
            path=output_pdf,
            width=WIDTH,
            height=HEIGHT,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
            scale=1,                     # no auto fit
        )
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python makepdf_sync.py input.html [output.pdf]")
        raise SystemExit(1)
    input_html = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else "slides.pdf"
    run(input_html, output_pdf)
