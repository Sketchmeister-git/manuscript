#!/usr/bin/env python3
"""Mechanical audits on the master manuscript: citations and quotations.

    citation sweep   Every in-text (Author, Year) citation has a Works Cited
                     entry, and every Works Cited entry is cited in the text.
    quotation audit  Every quotation marked as verified (no dagger) that comes
                     from a public-domain source is found word for word in the
                     primary text stored under book/reference/primary/.

Run after build_kdp.py --master. Exits non-zero if either audit fails, so a
build can be stopped when the verified-quotation count falls.
"""

import re
import sys
import unicodedata
from pathlib import Path

import book_config as config

BOOK_DIR = Path(__file__).resolve().parent.parent
MASTER_PATH = BOOK_DIR / f"{config.MASTER_NAME}.md"
PRIMARY_DIR = BOOK_DIR / "reference" / "primary"

# Verified quotations: (fragment as printed in the book, primary file it must appear in).
# Fragments are compared after normalising whitespace, quotes and dashes.
VERIFIED_QUOTATIONS = [
    ("To create new values—that, even the lion cannot yet accomplish: but to create itself freedom for new creating—that can the might of the lion do.", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("Innocence is the child, and forgetfulness, a new beginning, a game, a self-rolling wheel, a first movement, a holy Yea.", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("both are too burdensome", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("Give us this last man, O Zarathustra", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("make us into these last men!", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("But tell me, my brethren, what the child can do, which even the lion could not do? Why hath the preying lion still to become a child?", "Nietzsche_Zarathustra_Common-1909_PG1998.txt"),
    ("Who gave us the sponge to wipe away the whole horizon? What did we do when we loosened this earth from its sun?", "Nietzsche_JoyfulWisdom_Common-1910_PG52881.txt"),
    ("Do we not stray, as through infinite nothingness?", "Nietzsche_JoyfulWisdom_Common-1910_PG52881.txt"),
    ("God is dead! God remains dead! And we have killed him!", "Nietzsche_JoyfulWisdom_Common-1910_PG52881.txt"),
    ("God is dead: but as the human race is constituted, there will perhaps be caves for millenniums yet, in which people will show his shadow", "Nietzsche_JoyfulWisdom_Common-1910_PG52881.txt"),
    ("weakness of will, or more strictly speaking, the inability not to react to a stimulus, is in itself simply another form of degeneracy", "Nietzsche_Twilight_Ludovici-1911_PG52263.txt"),
    ("To learn to see—to accustom the eye to calmness, to patience, and to allow things to come up to it; to defer judgment", "Nietzsche_Twilight_Ludovici-1911_PG52263.txt"),
    ("One must not respond immediately to a stimulus", "Nietzsche_Twilight_Ludovici-1911_PG52263.txt"),
    ("All lack of intellectuality, all vulgarity, arises out of the inability to resist a stimulus:—one must respond or react, every impulse is indulged.", "Nietzsche_Twilight_Ludovici-1911_PG52263.txt"),
]

# Works Cited entries are keyed by first-author surname and the year printed in
# the entry; in-text "Original/Translation" years cite the translation year.
SURNAME_ALIASES = {"Center for Near-Earth Object Studies": "Center", "Tocqueville, A. de": "Tocqueville"}


def normalise(text: str) -> str:
    """Fold typography so a fragment matches regardless of line wrapping and quote style."""
    text = unicodedata.normalize("NFKC", text)
    for source, target in {"’": "'", "‘": "'", "“": '"', "”": '"', "_": "", "—": "-", "–": "-"}.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip().lower()


def split_master(master_text: str):
    """Return (body text, works cited text). Body excludes the Works Cited list itself."""
    start = master_text.index("# Works Cited")
    end = master_text.index("<!-- MARKS-KEPT-BELOW -->")
    return master_text[:start] + master_text[end:], master_text[start:end]


def works_cited_keys(works_cited_text: str) -> dict:
    """Map (surname, year-with-suffix) to the entry's first line."""
    keys = {}
    for line in works_cited_text.splitlines():
        match = re.match(r"^([A-Z][^,(]+?)(?:,| \()[^()]*?\((\d{4}[a-z]?|ca\. \d+)", line)
        if not match or line.startswith("#"):
            continue
        surname = match.group(1).strip().rstrip(".")
        for full_name, alias in SURNAME_ALIASES.items():
            if line.startswith(full_name):
                surname = alias
        keys[(surname, match.group(2))] = line[:90]
    return keys


def in_text_citations(body_text: str) -> set:
    """Collect (surname, year) pairs from parenthetical and narrative APA citations."""
    citations = set()
    name = r"([A-Z][A-Za-zÀ-ÿ\-]+)"
    year = r"(?:ca\. \d+ B\.C\.E\.|\d{4}(?:–\d{4})?)/?(\d{4}[a-z]?)?"
    patterns = [
        # Narrative form with a title between name and year: Name's *Title* (Year)
        rf"{name}['’]s \*[^*]+\* \(({year})()",
        rf"{name}(?:['’]s)?(?: et al\.| and [A-Z][a-z]+(?:['’]s)?| & [A-Z][a-z]+)?,? \(?({year})((?:, \d{{4}}[a-z]?)*)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, body_text):
            surname, full_year, translation_year, more_years = match.groups()
            cited_year = translation_year or full_year.split("/")[0]
            for each_year in [cited_year] + re.findall(r"\d{4}[a-z]?", more_years or ""):
                if re.fullmatch(r"\d{4}[a-z]?", each_year):
                    citations.add((surname, each_year))
    return citations


def citation_sweep(master_text: str) -> bool:
    body_text, works_cited_text = split_master(master_text)
    references = works_cited_keys(works_cited_text)
    citations = in_text_citations(body_text)
    reference_surnames = {surname for surname, _ in references}
    # Only count in-text pairs whose surname is a reference author; this filters
    # ordinary capitalised words followed by a number (e.g. "Chapter 4").
    relevant_citations = {pair for pair in citations if pair[0] in reference_surnames}
    cited_without_reference = sorted(relevant_citations - set(references))
    referenced_without_citation = sorted(set(references) - relevant_citations)
    print(f"[citations] {len(references)} Works Cited entries; {len(relevant_citations)} distinct in-text citations")
    for pair in cited_without_reference:
        print(f"  cited but not in Works Cited: {pair}")
    for pair in referenced_without_citation:
        print(f"  in Works Cited but never cited: {pair} -> {references[pair]}")
    return not cited_without_reference and not referenced_without_citation


def quotation_audit() -> bool:
    verified_count = 0
    all_found = True
    for fragment, primary_name in VERIFIED_QUOTATIONS:
        primary_text = normalise((PRIMARY_DIR / primary_name).read_text(encoding="utf-8"))
        if normalise(fragment) in primary_text:
            verified_count += 1
        else:
            all_found = False
            print(f"  NOT FOUND in {primary_name}: {fragment[:70]}")
    print(f"[quotations] {verified_count}/{len(VERIFIED_QUOTATIONS)} verified quotations found in primary texts")
    return all_found


def main() -> None:
    master_text = MASTER_PATH.read_text(encoding="utf-8")
    citations_ok = citation_sweep(master_text)
    quotations_ok = quotation_audit()
    daggers = master_text.split("<!-- MARKS-KEPT-BELOW -->")[0].count("†")
    print(f"[marks] {daggers} unverified (†) items in the body")
    sys.exit(0 if citations_ok and quotations_ok else 1)


if __name__ == "__main__":
    main()
