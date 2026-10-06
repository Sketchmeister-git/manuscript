#!/usr/bin/env python3
"""Mechanical audits on the master manuscript: citations and quotations.

    citation sweep   Every in-text (Author, Year) citation has a Works Cited
                     entry, and every Works Cited entry is cited in the text.
                     An author who is cited but has no entry at all is reported,
                     not skipped. Both "Surname, I. (Year)" and "Name. (Year)."
                     (single-name and organisation authors) entries are read.
    quotation audit  Every quotation marked as verified (no dagger) that comes
                     from a public-domain source is found word for word in the
                     primary text stored under book/reference/primary/, and the
                     same fragment is also printed in the master. A fragment
                     altered or removed in book/src/ therefore fails the audit.

Run after build_kdp.py --master. Exits non-zero if either audit fails, so a
build can be stopped when the verified-quotation count falls.

Not covered: a quotation printed in the book that is not listed in
VERIFIED_QUOTATIONS is not checked. Listing them automatically was tried and
dropped: the book's own Proposition blockquotes make any heuristic too noisy.
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

# Fragments listed above that the book does not currently print. They are
# acknowledged here so the audit stays green while the author decides, and are
# still reported on every run. Resolve each by re-adding the passage to its
# chapter in book/src/, or by deleting its VERIFIED_QUOTATIONS entry and then
# removing it from this set.
UNPRINTED_FRAGMENTS_ACKNOWLEDGED = {
    "But tell me, my brethren, what the child can do, which even the lion could not do? Why hath the preying lion still to become a child?",
}

# Works Cited entries are keyed by first-author surname and the year printed in
# the entry; in-text "Original/Translation" years cite the translation year.
# The same table folds an organisation's full in-text name to its key, so
# "(Center for Near-Earth Object Studies, 2026)" is read as ("Center", "2026").
SURNAME_ALIASES = {"Center for Near-Earth Object Studies": "Center", "Tocqueville, A. de": "Tocqueville"}

# "Surname, I. (Year)": personal authors. "Name. (Year).": a single-name author or
# an organisation (Aristotle, Laozi, Center for Near-Earth Object Studies).
AUTHOR_LIST_ENTRY = re.compile(r"^([A-Z][^,(]+?)(?:,| \()[^()]*?\((\d{4}[a-z]?|ca\. \d+)")
SINGLE_NAME_ENTRY = re.compile(r"^([A-Z][^,(]+?)\. \((\d{4}[a-z]?|ca\. \d+)")

# Capitalised words that precede a year without being an author ("since March, 2024").
NON_AUTHOR_WORDS = {
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
}


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
        match = AUTHOR_LIST_ENTRY.match(line) or SINGLE_NAME_ENTRY.match(line)
        if not match or line.startswith("#"):
            continue
        surname = match.group(1).strip().rstrip(".")
        for full_name, alias in SURNAME_ALIASES.items():
            if line.startswith(full_name):
                surname = alias
        keys[(surname, match.group(2))] = line[:90]
    return keys


def fold_author_aliases(text: str) -> str:
    """Replace an organisation's full in-text name with its Works Cited key."""
    for full_name, alias in SURNAME_ALIASES.items():
        text = text.replace(full_name, alias)
    return text


def in_text_citations(body_text: str) -> set:
    """Collect (surname, year) pairs from parenthetical and narrative APA citations.

    A name counts as cited only in citation form: a comma or an opening parenthesis
    must stand between the name and the year ("Fromm, 1941", "Libet et al. (1983)"),
    or the narrative form "Name's *Title* (Year)". That keeps dates such as
    "3 October 2026" out without consulting the Works Cited, so an author whose
    entry is missing cannot hide their own citations.
    """
    citations = set()
    body_text = fold_author_aliases(body_text)
    # A capitalised surname, optionally with an internal apostrophe (O'Brien); it
    # cannot start in the middle of a word.
    name = r"(?<![A-Za-zÀ-ÿ])([A-Z](?:[A-Za-zÀ-ÿ\-]+|['’][A-Z][A-Za-zÀ-ÿ\-]+))"
    year = r"(?:ca\. \d+ B\.C\.E\.|\d{4}(?:–\d{4})?)/?(\d{4}[a-z]?)?"
    patterns = [
        # Narrative form with a title between name and year: Name's *Title* (Year)
        rf"{name}['’]s \*[^*]+\* \(({year})()",
        rf"{name}(?:['’]s)?(?: et al\.| and [A-Z][a-z]+(?:['’]s)?| & [A-Z][a-z]+)?(?:,\s+|\s+\()({year})((?:, \d{{4}}[a-z]?)*)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, body_text):
            surname, full_year, translation_year, more_years = match.groups()
            if surname in NON_AUTHOR_WORDS:
                continue
            cited_year = translation_year or full_year.split("/")[0]
            for each_year in [cited_year] + re.findall(r"\d{4}[a-z]?", more_years or ""):
                if re.fullmatch(r"\d{4}[a-z]?", each_year):
                    citations.add((surname, each_year))
    return citations


def citation_sweep(master_text: str) -> bool:
    body_text, works_cited_text = split_master(master_text)
    references = works_cited_keys(works_cited_text)
    # Every citation counts, including one whose author has no Works Cited entry
    # at all: that is exactly the omission this sweep exists to catch.
    citations = in_text_citations(body_text)
    cited_without_reference = sorted(citations - set(references))
    referenced_without_citation = sorted(set(references) - citations)
    print(f"[citations] {len(references)} Works Cited entries; {len(citations)} distinct in-text citations")
    for pair in cited_without_reference:
        print(f"  cited but not in Works Cited: {pair}")
    for pair in referenced_without_citation:
        print(f"  in Works Cited but never cited: {pair} -> {references[pair]}")
    return not cited_without_reference and not referenced_without_citation


def printed_book_text(master_text: str) -> str:
    """The master as a reader sees it, normalised: no blockquote markers, emphasis
    stars or † ‡ marks, so a fragment matches whether the book quotes it inline,
    in a blockquote, in italics or with a verification mark beside it."""
    without_blockquote_markers = re.sub(r"(?m)^[ \t]*>[ \t]?", "", master_text)
    without_markup = re.sub(r"[*†‡]", "", without_blockquote_markers)
    return normalise(without_markup)


def quotation_audit(master_text: str) -> bool:
    """Check each listed fragment against its primary text and against the book."""
    book_text = printed_book_text(master_text)
    found_in_primary_count = 0
    printed_in_book_count = 0
    acknowledged_unprinted = []
    all_ok = True
    for fragment, primary_name in VERIFIED_QUOTATIONS:
        normalised_fragment = normalise(fragment)
        primary_text = normalise((PRIMARY_DIR / primary_name).read_text(encoding="utf-8"))
        if normalised_fragment in primary_text:
            found_in_primary_count += 1
        else:
            all_ok = False
            print(f"  NOT FOUND in {primary_name}: {fragment[:70]}")
        is_printed = normalised_fragment in book_text
        if is_printed:
            printed_in_book_count += 1
        if fragment in UNPRINTED_FRAGMENTS_ACKNOWLEDGED:
            if is_printed:
                print(f"  note: now printed in the book; remove it from UNPRINTED_FRAGMENTS_ACKNOWLEDGED: {fragment[:70]}")
            else:
                acknowledged_unprinted.append(fragment)
        elif not is_printed:
            all_ok = False
            print(f"  NOT PRINTED in the book (changed or removed in book/src/?): {fragment[:70]}")
    print(f"[quotations] {found_in_primary_count}/{len(VERIFIED_QUOTATIONS)} verified quotations found in primary texts")
    print(f"[quotations] {printed_in_book_count}/{len(VERIFIED_QUOTATIONS)} listed fragments printed in the book")
    for fragment in acknowledged_unprinted:
        print(f"  acknowledged, not printed in the book (author to decide): {fragment[:70]}")
    return all_ok


def main() -> None:
    master_text = MASTER_PATH.read_text(encoding="utf-8")
    citations_ok = citation_sweep(master_text)
    quotations_ok = quotation_audit(master_text)
    daggers = master_text.split("<!-- MARKS-KEPT-BELOW -->")[0].count("†")
    print(f"[marks] {daggers} unverified (†) items in the body")
    sys.exit(0 if citations_ok and quotations_ok else 1)


if __name__ == "__main__":
    main()
