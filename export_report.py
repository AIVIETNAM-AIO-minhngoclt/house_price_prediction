#!/usr/bin/env python3
"""Export the lab notebook to a self-contained HTML page and a printable PDF.

Run:  python3 export_report.py

Two fixes are applied to nbconvert's HTML before printing, both of which the
default export gets wrong for this report:

1. MathJax inline math.  nbconvert configures MathJax with ``inlineMath:
   [['$','$'], ...]`` while its markdown renderer has *already* turned every
   escaped ``\\$`` in the source into a bare ``$``.  MathJax therefore pairs up
   the dollar signs in prose such as "adds $52.97 ... $22,708.55 ..." and
   typesets everything between them as a formula, silently deleting the text.
   Removing the ``['$','$']`` delimiter pair leaves prose dollars alone;
   ``$$...$$`` display math still works.
2. Print layout.  Long code lines are clipped at the page edge unless ``pre``
   is allowed to wrap, and figures/tables need to be kept off page breaks.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOTEBOOK = HERE / "Lab03_1_Linear_Regression_House_Prices.ipynb"
HTML_OUT = HERE / "Lab03_1_Linear_Regression_House_Prices.html"
PDF_OUT = HERE / "Lab03_1_Linear_Regression_House_Prices_Report.pdf"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]

PRINT_CSS = """
<style id="print-fixes">
@page { size: A4; margin: 13mm 11mm; }
body { background: #fff !important; }
pre, code, .jp-RenderedText pre, .CodeMirror-line, .jp-InputArea-editor {
  white-space: pre-wrap !important; word-break: break-word !important;
  overflow-wrap: anywhere !important; }
.jp-OutputArea-output, .jp-InputArea-editor { overflow: visible !important; max-width: 100% !important; }
img { max-width: 100% !important; height: auto !important; break-inside: avoid; }
table { break-inside: auto; font-size: 11px; }
tr, img, .jp-RenderedImage { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }
.jp-Notebook { padding: 0 !important; }
</style>
"""

# The delimiter pair that makes MathJax eat dollar amounts, and its replacement.
MATHJAX_BAD = """inlineMath: [ ['$','$'], ["\\\\(","\\\\)"] ],"""
MATHJAX_FIXED = """inlineMath: [ ["\\\\(","\\\\)"] ],"""


def build_html() -> None:
    subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert", "--to", "html",
         "--template", "lab", "--embed-images",
         "--output", str(HTML_OUT), str(NOTEBOOK)],
        check=True,
    )
    html = HTML_OUT.read_text()

    if MATHJAX_BAD in html:
        html = html.replace(MATHJAX_BAD, MATHJAX_FIXED)
        print("  - disabled single-$ inline math (keeps dollar amounts intact)")
    else:
        print("  ! MathJax inline-math config not found; check nbconvert version", file=sys.stderr)

    html = html.replace("</head>", PRINT_CSS + "</head>", 1)
    HTML_OUT.write_text(html)
    print(f"  - wrote {HTML_OUT.name} ({HTML_OUT.stat().st_size/1e6:.1f} MB)")


def build_pdf() -> None:
    chrome = next((c for c in CHROME_CANDIDATES if c and pathlib.Path(c).exists()), None)
    if chrome is None:
        print("  ! No Chrome/Chromium found - open the HTML and print to PDF manually.", file=sys.stderr)
        return
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         "--run-all-compositor-stages-before-draw", "--virtual-time-budget=25000",
         f"--print-to-pdf={PDF_OUT}", HTML_OUT.as_uri()],
        check=True, capture_output=True,
    )
    print(f"  - wrote {PDF_OUT.name} ({PDF_OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    print(f"Exporting {NOTEBOOK.name}")
    build_html()
    build_pdf()
    print("Done.")
