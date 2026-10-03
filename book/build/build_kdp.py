#!/usr/bin/env python3
"""Build the KDP paperback interior PDF for The Lion's Problem.

Pipeline (each step is a separate function so it can be run or tested alone):

    1. assemble_master()        src/*.md  ->  book/<MASTER_NAME>.md   (source of record)
    2. prepare_print_markdown() strip † ‡ above the MARKS-KEPT-BELOW line, add index
                                markers to the main matter, set Works Cited layout
    3. run_pandoc()             markdown -> LaTeX (book class, 11pt, twoside, openright)
    4. run_xelatex()            three XeLaTeX passes with makeindex between them
    5. run_checks()             trim size, embedded fonts, missing glyphs, overfull boxes

The build never edits the master; it writes intermediates to build/out/.

Usage:  python3 build_kdp.py            (full build)
        python3 build_kdp.py --master   (assemble the master only)
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import book_config as config
from index_terms import INDEX_TERMS

BUILD_DIR = Path(__file__).resolve().parent
BOOK_DIR = BUILD_DIR.parent
SOURCE_DIR = BOOK_DIR / "src"
OUTPUT_DIR = BOOK_DIR / "output"
WORK_DIR = BUILD_DIR / "out"
MASTER_PATH = BOOK_DIR / f"{config.MASTER_NAME}.md"

MARKS_KEPT_MARKER = "<!-- MARKS-KEPT-BELOW -->"
MAINMATTER_MARKER = "\\realmainmatter"
BACKMATTER_MARKER = "\\backmatter"
VERIFICATION_MARKS = ("†", "‡")


# ---------------------------------------------------------------------------
# 1. Master assembly
# ---------------------------------------------------------------------------

def assemble_master() -> str:
    """Concatenate the chapter sources, in filename order, into the master file."""
    source_files = sorted(SOURCE_DIR.glob("*.md"))
    if not source_files:
        sys.exit(f"No sources found in {SOURCE_DIR}")
    master_text = "\n\n".join(path.read_text(encoding="utf-8").rstrip() for path in source_files) + "\n"
    MASTER_PATH.write_text(master_text, encoding="utf-8")
    print(f"[master] {MASTER_PATH.name}: {len(master_text.split())} words from {len(source_files)} files")
    return master_text


# ---------------------------------------------------------------------------
# 2. Print preparation (never touches the master)
# ---------------------------------------------------------------------------

def strip_marks_above_marker(markdown_text: str) -> str:
    """Remove verification marks from the body; the appendix keeps them."""
    if MARKS_KEPT_MARKER not in markdown_text:
        sys.exit("MARKS-KEPT-BELOW marker missing from master; refusing to strip marks blindly.")
    body, kept = markdown_text.split(MARKS_KEPT_MARKER, 1)
    for mark in VERIFICATION_MARKS:
        body = body.replace(mark, "")
    return body + MARKS_KEPT_MARKER + kept


def is_indexable_paragraph(paragraph: str) -> bool:
    """Index only running prose: skip headings, tables, raw LaTeX and fenced blocks."""
    first_line = paragraph.lstrip().split("\n", 1)[0]
    skip_prefixes = ("#", "|", "```", ":", "\\", "<!--")
    return bool(first_line) and not first_line.startswith(skip_prefixes)


def insert_index_markers(paragraph: str) -> str:
    """Append one \\index{} marker after the first match of each term in a paragraph."""
    for index_key, pattern in INDEX_TERMS.items():
        match = re.search(pattern, paragraph)
        if not match:
            continue
        # Move to the end of the word so the marker never splits a token.
        end_position = match.end()
        while end_position < len(paragraph) and (paragraph[end_position].isalnum() or paragraph[end_position] in "-'’"):
            end_position += 1
        marker = f"`\\index{{{index_key}}}`{{=latex}}"
        paragraph = paragraph[:end_position] + marker + paragraph[end_position:]
    return paragraph


def add_index_to_main_matter(markdown_text: str) -> str:
    """Insert index markers only between \\mainmatter and \\backmatter."""
    start = markdown_text.index(MAINMATTER_MARKER)
    end = markdown_text.index(BACKMATTER_MARKER)
    before, main_matter, after = markdown_text[:start], markdown_text[start:end], markdown_text[end:]

    indexed_blocks = []
    # The main matter begins inside a raw-LaTeX fence, so carry the fence state over.
    inside_fence = before.count("```") % 2 == 1
    for block in main_matter.split("\n\n"):
        fence_count = block.count("```")
        if not inside_fence and is_indexable_paragraph(block):
            indexed_blocks.append(insert_index_markers(block))
        else:
            indexed_blocks.append(block)
        if fence_count % 2 == 1:
            inside_fence = not inside_fence
    return before + "\n\n".join(indexed_blocks) + after


def set_works_cited_layout(markdown_text: str) -> str:
    """Replace the fenced div around the Works Cited with a hanging-indent environment."""
    opening = "::: {.hangingindent}"
    if opening not in markdown_text:
        return markdown_text
    markdown_text = markdown_text.replace(opening, "```{=latex}\n\\begin{hangingrefs}\n```", 1)
    closing_index = markdown_text.index("\n:::\n", markdown_text.index("\\begin{hangingrefs}"))
    return markdown_text[:closing_index] + "\n```{=latex}\n\\end{hangingrefs}\n```\n" + markdown_text[closing_index + 5:]


def fill_placeholders(template_text: str) -> str:
    """Substitute @@NAME@@ placeholders with values from book_config."""
    replacements = {
        "@@TITLE@@": config.BOOK_TITLE,
        "@@SUBTITLE@@": config.BOOK_SUBTITLE,
        "@@AUTHOR@@": config.AUTHOR_NAME,
        "@@EDITION@@": config.EDITION_LABEL,
        "@@VERSION@@": config.VERSION_LABEL,
        "@@YEAR@@": config.PUBLICATION_YEAR,
        "@@ISBN@@": config.ISBN_PAPERBACK,
    }
    for placeholder, value in replacements.items():
        template_text = template_text.replace(placeholder, value.replace("'", "’"))
    return template_text


def prepare_print_markdown(master_text: str) -> Path:
    """Write the print-ready markdown and filled LaTeX includes into the work directory."""
    WORK_DIR.mkdir(exist_ok=True)
    print_text = strip_marks_above_marker(master_text)
    print_text = add_index_to_main_matter(print_text)
    print_text = set_works_cited_layout(print_text)
    print_path = WORK_DIR / "print.md"
    print_path.write_text(print_text, encoding="utf-8")
    for include_name in ("header.tex", "frontmatter.tex"):
        filled = fill_placeholders((BUILD_DIR / include_name).read_text(encoding="utf-8"))
        (WORK_DIR / include_name).write_text(filled, encoding="utf-8")
    (WORK_DIR / "backmatter.tex").write_text("\\printindex\n", encoding="utf-8")
    return print_path


# ---------------------------------------------------------------------------
# 3–4. Typesetting
# ---------------------------------------------------------------------------

def run_command(command: list, working_directory: Path) -> subprocess.CompletedProcess:
    """Run a build command and stop the build with its output if it fails."""
    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-4000:], result.stderr[-4000:])
        sys.exit(f"Command failed: {' '.join(command)}")
    return result


def run_pandoc(print_path: Path) -> Path:
    """Convert the print markdown to a LaTeX book."""
    tex_path = WORK_DIR / "book.tex"
    geometry = (
        f"paperwidth={config.TRIM_WIDTH_IN}in,paperheight={config.TRIM_HEIGHT_IN}in,"
        f"inner={config.INNER_MARGIN_IN}in,outer={config.OUTER_MARGIN_IN}in,"
        f"top={config.TOP_MARGIN_IN}in,bottom={config.BOTTOM_MARGIN_IN}in,"
        "headsep=0.25in,footskip=0.4in"
    )
    run_command([
        "pandoc", str(print_path), "-o", str(tex_path), "--standalone",
        "--from=markdown+raw_tex-implicit_figures",
        "--top-level-division=chapter",
        "--pdf-engine=xelatex",
        "-V", "documentclass=book",
        "-V", "classoption=11pt,twoside,openright",
        "-V", f"geometry={geometry}",
        "--number-sections",
        "-V", "secnumdepth=0",
        "-V", "colorlinks=false",
        "-V", "linkcolor=black",
        "-H", str(WORK_DIR / "header.tex"),
        "-B", str(WORK_DIR / "frontmatter.tex"),
        "-A", str(WORK_DIR / "backmatter.tex"),
    ], WORK_DIR)
    return tex_path


def run_xelatex(tex_path: Path) -> Path:
    """Three XeLaTeX passes (contents, cross-references) with makeindex in between."""
    for pass_number in range(1, 4):
        run_command(["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name], WORK_DIR)
        if pass_number == 1 and (WORK_DIR / "book.idx").exists():
            run_command(["makeindex", "book.idx"], WORK_DIR)
    pdf_path = WORK_DIR / "book.pdf"
    OUTPUT_DIR.mkdir(exist_ok=True)
    final_path = OUTPUT_DIR / f"{config.MASTER_NAME}_KDP-Interior.pdf"
    shutil.copyfile(pdf_path, final_path)
    return final_path


# ---------------------------------------------------------------------------
# 5. Post-build checks
# ---------------------------------------------------------------------------

def run_checks(pdf_path: Path) -> dict:
    """Check trim size, font embedding, missing glyphs and overfull boxes."""
    import fitz  # PyMuPDF

    report = {}
    document = fitz.open(pdf_path)
    report["pages"] = document.page_count
    first_page = document[0].rect
    report["trim_in"] = (round(first_page.width / 72, 3), round(first_page.height / 72, 3))
    report["trim_ok"] = report["trim_in"] == (config.TRIM_WIDTH_IN, config.TRIM_HEIGHT_IN)

    font_listing = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True).stdout
    font_rows = font_listing.splitlines()[2:]
    report["fonts_not_embedded"] = [row for row in font_rows if row.split()[-5:-4] != ["yes"]]

    log_text = (WORK_DIR / "book.log").read_text(encoding="utf-8", errors="replace")
    report["missing_glyphs"] = sorted(set(re.findall(r"Missing character: There is no (.+?) in font", log_text)))
    overfull = [float(points) for points in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log_text)]
    report["overfull_over_10pt"] = len([points for points in overfull if points > 10])
    report["overfull_total"] = len(overfull)
    report["undefined_references"] = "There were undefined references" in log_text

    spine_white = report["pages"] * config.SPINE_PER_PAGE_WHITE_IN
    spine_cream = report["pages"] * config.SPINE_PER_PAGE_CREAM_IN
    report["spine_in_white"] = round(spine_white, 4)
    report["spine_in_cream"] = round(spine_cream, 4)
    return report


def main() -> None:
    master_text = assemble_master()
    if "--master" in sys.argv:
        return
    print_path = prepare_print_markdown(master_text)
    tex_path = run_pandoc(print_path)
    pdf_path = run_xelatex(tex_path)
    report = run_checks(pdf_path)
    print(f"[pdf] {pdf_path}")
    for key, value in report.items():
        print(f"  {key}: {value}")
    (WORK_DIR / "build_report.txt").write_text("\n".join(f"{k}: {v}" for k, v in report.items()), encoding="utf-8")


if __name__ == "__main__":
    main()
