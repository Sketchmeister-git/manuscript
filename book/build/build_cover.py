#!/usr/bin/env python3
"""Build the KDP paperback wrap cover (PDF) and the Kindle eBook cover (JPEG).

The paperback wrap is sized from the interior page count, because KDP's spine
width depends on it: spine = pages x paper thickness. Run build_kdp.py first so
the interior PDF exists, then run this script.

Outputs (book/output/):
    <MASTER_NAME>_Cover-Paperback-Wrap.pdf   full wrap with 0.125 in bleed
    <MASTER_NAME>_Cover-Front.pdf            front panel only, trim size
    <MASTER_NAME>_Cover-eBook.jpg            1600 x 2400 px (6 x 9 ratio; KDP accepts it,
                                             its ideal is 1:1.6)
"""

import subprocess
import sys
from pathlib import Path

import pymupdf

import book_config as config

BUILD_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BUILD_DIR.parent / "output"
WORK_DIR = BUILD_DIR / "out"
INTERIOR_PDF = OUTPUT_DIR / f"{config.MASTER_NAME}_KDP-Interior.pdf"

PAPER = "cream"                       # AUTHOR: "white" or "cream"; must match the KDP setting
MINIMUM_PAGES_FOR_SPINE_TEXT = 79     # KDP rule

BACK_COVER_BLURB = (
    "Why does a critique that nearly everyone accepts change almost nothing?\\par\\medskip "
    "We are asked to hold a view on every catastrophe and given the power to act on almost none. "
    "Drawing on Nietzsche and Fromm, phenomenology and experimental psychology, clinical ethics and "
    "political theory, this book argues that the strain is not cognitive dissonance but "
    "responsibility without efficacy, and that a culture fluent only in refusal, facing an "
    "authority with no face, reaches for a villain or for an agentless noun. Neither meets the need.\\par\\medskip "
    "The way out is not better beliefs or stronger resolve. It is better arrangements: "
    "the slow, unglamorous work of building norms in a medium that has had only twenty-five years "
    "to develop any, and the willingness to be bad at something in public for a while."
)

AUTHOR_BIO = "[AUTHOR: two or three sentences of biography go here.]"

# Palette: deep ink ground, warm parchment type, muted gold rule.
GROUND_RGB = "29,36,48"
TYPE_RGB = "236,228,210"
ACCENT_RGB = "184,150,86"


def spine_width_inches(page_count: int) -> float:
    """KDP spine width for the chosen paper stock."""
    per_page = config.SPINE_PER_PAGE_CREAM_IN if PAPER == "cream" else config.SPINE_PER_PAGE_WHITE_IN
    return page_count * per_page


def latex_escape_apostrophe(text: str) -> str:
    """Use typographic apostrophes so XeLaTeX prints them correctly."""
    return text.replace("'", "’")


def front_panel_tikz(left_x: float) -> str:
    """Front panel artwork: title, subtitle, author, and an empty oval (the faceless authority)."""
    title = latex_escape_apostrophe(config.BOOK_TITLE)
    # Break the subtitle at its comma-and so the line never hyphenates.
    subtitle = config.BOOK_SUBTITLE.replace(", and ", ",\\\\ and ", 1)
    author = config.AUTHOR_NAME
    centre_x = left_x + config.TRIM_WIDTH_IN / 2
    return rf"""
  % Front panel
  \node[text=typec, font=\fontsize{{40}}{{44}}\selectfont\itshape, align=center, text width=5in]
       at ({centre_x}in, 7.45in) {{{title}}};
  \draw[accent, line width=0.8pt] ({centre_x - 0.9}in, 6.85in) -- ({centre_x + 0.9}in, 6.85in);
  \node[text=typec, font=\fontsize{{13}}{{17}}\selectfont, align=center, text width=4.4in]
       at ({centre_x}in, 6.35in) {{{subtitle}}};
  \draw[typec, line width=1.1pt] ({centre_x}in, 3.75in) ellipse (0.95in and 1.25in);
  \draw[accent, line width=0.5pt] ({centre_x}in, 3.75in) ellipse (1.12in and 1.42in);
  \node[text=typec, font=\fontsize{{15}}{{18}}\selectfont\scshape, align=center]
       at ({centre_x}in, 1.05in) {{\MakeLowercase{{{author}}}}};
"""


def cover_document(page_count: int, wrap: bool) -> str:
    """Return a complete XeLaTeX document for the wrap or the front panel alone."""
    bleed = config.COVER_BLEED_IN if wrap else 0.0
    spine = spine_width_inches(page_count) if wrap else 0.0
    trim_w, trim_h = config.TRIM_WIDTH_IN, config.TRIM_HEIGHT_IN
    paper_w = (2 * trim_w + spine + 2 * bleed) if wrap else trim_w
    paper_h = trim_h + 2 * bleed

    # In wrap mode the origin is the bottom-left corner of the back panel's trim.
    front_left = (trim_w + spine) if wrap else 0.0
    parts = [front_panel_tikz(front_left)]

    if wrap:
        back_centre = trim_w / 2
        parts.append(rf"""
  % Back panel: blurb, author bio, barcode clear area (2 x 1.2 in, bottom right).
  \node[text=typec, font=\fontsize{{11}}{{15}}\selectfont, align=justify, text width=4.4in, anchor=north]
       at ({back_centre}in, 8.1in) {{{BACK_COVER_BLURB}}};
  \node[text=typec, font=\fontsize{{9}}{{12}}\selectfont\itshape, align=left, text width=4.4in, anchor=north]
       at ({back_centre}in, 3.3in) {{{AUTHOR_BIO}}};
  \fill[white] ({trim_w - 0.25 - 2.0}in, 0.25in) rectangle ({trim_w - 0.25}in, 1.45in);
""")
        if page_count >= MINIMUM_PAGES_FOR_SPINE_TEXT:
            spine_centre = trim_w + spine / 2
            spine_title = latex_escape_apostrophe(config.BOOK_TITLE)
            parts.append(rf"""
  % Spine (KDP allows spine text from {MINIMUM_PAGES_FOR_SPINE_TEXT} pages)
  \node[text=typec, rotate=-90, font=\fontsize{{9.5}}{{11}}\selectfont]
       at ({spine_centre}in, {trim_h / 2}in) {{\textit{{{spine_title}}}\quad\textcolor{{accent}}{{\textbullet}}\quad\textsc{{\MakeLowercase{{{config.AUTHOR_NAME}}}}}}};
""")

    return rf"""\documentclass{{article}}
\usepackage[paperwidth={paper_w}in,paperheight={paper_h}in,margin=0in]{{geometry}}
\usepackage{{fontspec}}
\setmainfont{{TeX Gyre Pagella}}
\usepackage{{tikz}}
\definecolor{{ground}}{{RGB}}{{{GROUND_RGB}}}
\definecolor{{typec}}{{RGB}}{{{TYPE_RGB}}}
\definecolor{{accent}}{{RGB}}{{{ACCENT_RGB}}}
\pagestyle{{empty}}
\hyphenpenalty=10000
\begin{{document}}
\begin{{tikzpicture}}[remember picture, overlay, x=1in, y=1in, shift={{(current page.south west)}}, shift={{({bleed}in,{bleed}in)}}]
  \fill[ground] ({-bleed}in, {-bleed}in) rectangle ({paper_w - bleed}in, {paper_h - bleed}in);
{''.join(parts)}
\end{{tikzpicture}}
\end{{document}}
"""


def compile_cover(document_text: str, job_name: str) -> Path:
    """Compile one cover document with XeLaTeX and copy it to the output folder."""
    tex_path = WORK_DIR / f"{job_name}.tex"
    tex_path.write_text(document_text, encoding="utf-8")
    for _ in range(2):  # remember picture needs two passes
        result = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                                cwd=WORK_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout[-3000:])
            sys.exit(f"Cover build failed: {job_name}")
    final_path = OUTPUT_DIR / f"{config.MASTER_NAME}_{job_name}.pdf"
    final_path.write_bytes((WORK_DIR / f"{job_name}.pdf").read_bytes())
    return final_path


def render_ebook_jpeg(front_pdf: Path) -> Path:
    """Render the front panel 1600 px wide (2400 px tall at the 6 x 9 trim ratio)."""
    document = pymupdf.open(front_pdf)
    zoom = 1600 / document[0].rect.width
    pixmap = document[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    jpeg_path = OUTPUT_DIR / f"{config.MASTER_NAME}_Cover-eBook.jpg"
    pixmap.save(jpeg_path, jpg_quality=92)
    return jpeg_path


def main() -> None:
    if not INTERIOR_PDF.exists():
        sys.exit("Build the interior first (build_kdp.py); the spine width depends on its page count.")
    WORK_DIR.mkdir(exist_ok=True)
    page_count = pymupdf.open(INTERIOR_PDF).page_count
    wrap_pdf = compile_cover(cover_document(page_count, wrap=True), "Cover-Paperback-Wrap")
    front_pdf = compile_cover(cover_document(page_count, wrap=False), "Cover-Front")
    jpeg_path = render_ebook_jpeg(front_pdf)
    wrap_rect = pymupdf.open(wrap_pdf)[0].rect
    print(f"[cover] interior pages: {page_count}; paper: {PAPER}; spine: {spine_width_inches(page_count):.4f} in")
    print(f"[cover] wrap: {wrap_rect.width / 72:.3f} x {wrap_rect.height / 72:.3f} in -> {wrap_pdf.name}")
    print(f"[cover] front: {front_pdf.name}; eBook: {jpeg_path.name}")


if __name__ == "__main__":
    main()
