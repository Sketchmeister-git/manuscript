#!/usr/bin/env python3
"""Build the EPUB (Kindle eBook) and Word (.docx) editions from the master.

Both formats reflow, so they differ from the print PDF in three ways:

    * no running heads, page numbers or back-of-book index (an index keyed to page
      numbers means nothing in a reflowable file; the Glossary and contents stay);
    * the half-title, copyright page and epigraph, which the PDF typesets from
      frontmatter.tex, are written here as markdown from book_config.py;
    * parts and chapter numbers, which LaTeX supplies, are written into the headings.

Verification marks (dagger, double dagger) are stripped from the body exactly as in
the PDF build, and kept in the appendix. The master is never edited.

Usage:  python3 build_formats.py          (EPUB and DOCX)
        python3 build_formats.py --check  (also re-reads both files and reports headings)
"""

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import book_config as config
from build_kdp import MASTER_PATH, OUTPUT_DIR, WORK_DIR, strip_marks_above_marker

ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
EPUB_COVER = OUTPUT_DIR / f"{config.MASTER_NAME}_Cover-eBook.jpg"
LATEX_FENCE = re.compile(r"```\{=latex\}\n(.*?)\n```\n?", re.DOTALL)
PART_COMMAND = re.compile(r"\\part\{([^}]*)\}")


def front_matter_markdown() -> str:
    """Title page, copyright page and epigraph, as markdown, from book_config."""
    return f"""---
title: "{config.BOOK_TITLE}"
subtitle: "{config.BOOK_SUBTITLE}"
author: "{config.AUTHOR_NAME}"
lang: en-US
rights: "Copyright © {config.PUBLICATION_YEAR} {config.AUTHOR_NAME}. All rights reserved."
---

# Copyright {{.unnumbered}}

*{config.BOOK_TITLE}: {config.BOOK_SUBTITLE}*

Copyright © {config.PUBLICATION_YEAR} {config.AUTHOR_NAME}. All rights reserved.

No part of this book may be reproduced in any form without written permission from the author, except for brief quotations in reviews and scholarly works.

Quotations from Nietzsche and Tocqueville are taken from translations in the public domain, as transcribed by Project Gutenberg, and are cited in the Works Cited. All other quotations are brief and are used for criticism and commentary.

This book discusses psychological research for general and scholarly readers. It is not clinical advice.

ISBN: {config.ISBN_PAPERBACK}

{config.EDITION_LABEL}, {config.PUBLICATION_YEAR} ({config.VERSION_LABEL}). Independently published.

# Epigraph {{.unnumbered}}

> *But tell me, my brethren, what the child can do, which even the lion could not do? Why hath the preying lion still to become a child?*
>
> — Friedrich Nietzsche, *Thus Spake Zarathustra* (trans. Thomas Common)

"""


def convert_parts_and_chapter_numbers(markdown_text: str) -> str:
    """Write parts and chapter numbers into the headings, since LaTeX is not there to.

    A raw-LaTeX part command becomes a heading "Part I: Title". Every numbered
    top-level heading (one without {.unnumbered}) becomes "1. Title", counting up.
    All other raw-LaTeX blocks are dropped (pandoc ignores them in these formats,
    but removing them keeps the markdown clean and the line breaks predictable).
    """
    part_count = 0

    def replace_fence(match: re.Match) -> str:
        nonlocal part_count
        part_match = PART_COMMAND.search(match.group(1))
        if part_match:
            part_count += 1
            return f"# Part {ROMAN_NUMERALS[part_count - 1]}: {part_match.group(1)} {{.unnumbered}}\n\n"
        return ""

    text = LATEX_FENCE.sub(replace_fence, markdown_text)
    chapter_count = 0
    numbered_lines = []
    for line in text.split("\n"):
        is_chapter = line.startswith("# ") and "{.unnumbered" not in line
        if is_chapter:
            chapter_count += 1
            line = f"# {chapter_count}. {line[2:]}"
        numbered_lines.append(line)
    return "\n".join(numbered_lines)


def remove_print_only_markup(markdown_text: str) -> str:
    """Drop raw TeX that is not inside a fence (spacing commands) and the print-only wrappers."""
    markdown_text = re.sub(r"(?m)^\\vspace\{[^}]*\}\s*$\n?", "", markdown_text)
    markdown_text = markdown_text.replace("::: {.hangingindent}", "").replace("\n:::\n", "\n")
    return markdown_text


def prepare_reflowable_markdown() -> Path:
    """Write the markdown shared by the EPUB and DOCX builds."""
    master_text = MASTER_PATH.read_text(encoding="utf-8")
    body = strip_marks_above_marker(master_text).replace("<!-- MARKS-KEPT-BELOW -->", "")
    body = remove_print_only_markup(convert_parts_and_chapter_numbers(body))
    WORK_DIR.mkdir(exist_ok=True)
    output_path = WORK_DIR / "reflowable.md"
    output_path.write_text(front_matter_markdown() + body, encoding="utf-8")
    return output_path


def run_pandoc(arguments: list) -> None:
    result = subprocess.run(["pandoc"] + arguments, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:], result.stderr[-3000:])
        sys.exit("pandoc failed: " + " ".join(arguments[:6]))
    if result.stderr.strip():
        print("  pandoc notes:", result.stderr.strip()[:500])


def build_epub(markdown_path: Path) -> Path:
    """EPUB 3 with a contents page, cover image and the book's own stylesheet."""
    stylesheet = WORK_DIR / "epub.css"
    stylesheet.write_text(
        "body { font-family: serif; line-height: 1.45; }\n"
        "h1 { text-align: center; font-style: italic; font-weight: normal; margin: 2em 0 1em; page-break-before: always; }\n"
        "h2 { font-size: 1.15em; margin-top: 1.6em; }\n"
        "h3 { font-size: 1em; font-style: italic; }\n"
        "blockquote { margin: 1em 1.5em; font-size: 0.95em; }\n"
        "table { border-collapse: collapse; margin: 1em 0; font-size: 0.9em; }\n"
        "th, td { border-bottom: 1px solid #999; padding: 0.25em 0.5em; text-align: left; vertical-align: top; }\n"
        "dt { font-weight: bold; margin-top: 0.8em; }\n",
        encoding="utf-8",
    )
    epub_path = OUTPUT_DIR / f"{config.MASTER_NAME}.epub"
    arguments = [str(markdown_path), "-o", str(epub_path), "--from=markdown-implicit_figures-raw_tex",
                 "--to=epub3", "--toc", "--toc-depth=1", "--split-level=1", f"--css={stylesheet}",
                 "--metadata=lang:en-US"]
    if EPUB_COVER.exists():
        arguments.append(f"--epub-cover-image={EPUB_COVER}")
    run_pandoc(arguments)
    return epub_path


def build_docx(markdown_path: Path) -> Path:
    """Word manuscript with a table of contents and styled headings."""
    docx_path = OUTPUT_DIR / f"{config.MASTER_NAME}.docx"
    run_pandoc([str(markdown_path), "-o", str(docx_path), "--from=markdown-implicit_figures-raw_tex",
                "--to=docx", "--toc", "--toc-depth=1", "--metadata=lang:en-US"])
    return docx_path


def check_outputs(epub_path: Path, docx_path: Path) -> None:
    """Re-open both files and report their headings, so a bad conversion is visible."""
    with zipfile.ZipFile(epub_path) as archive:
        names = archive.namelist()
        chapter_files = [name for name in names if name.startswith("EPUB/text/") and name.endswith(".xhtml")]
        heading_count = sum(len(re.findall(r"<h1[ >]", archive.read(name).decode("utf-8"))) for name in chapter_files)
        has_cover = any("cover" in name.lower() for name in names)
    print(f"[epub] {epub_path.name}: {epub_path.stat().st_size // 1024} KB, {len(chapter_files)} sections, "
          f"{heading_count} chapter headings, cover image: {has_cover}")
    with zipfile.ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    heading_one_count = len(re.findall(r'w:pStyle w:val="Heading1"', document_xml))
    stray_marks = document_xml.count("†") + document_xml.count("‡")
    print(f"[docx] {docx_path.name}: {docx_path.stat().st_size // 1024} KB, {heading_one_count} Heading 1 paragraphs, "
          f"† ‡ marks in file: {stray_marks} (expected: only in Appendix E)")


def main() -> None:
    if not MASTER_PATH.exists():
        sys.exit("Run build_kdp.py --master first.")
    OUTPUT_DIR.mkdir(exist_ok=True)
    markdown_path = prepare_reflowable_markdown()
    epub_path = build_epub(markdown_path)
    docx_path = build_docx(markdown_path)
    print(f"[formats] {epub_path.name}\n[formats] {docx_path.name}")
    if "--check" in sys.argv:
        check_outputs(epub_path, docx_path)


if __name__ == "__main__":
    main()
