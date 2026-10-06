# CLAUDE.md

*The Lion's Problem: Refusal, Anonymous Authority, and the Capacity to Build*: a philosophical manuscript built into a KDP paperback (6 × 9 in). `README.md` has the file map. This is a writing project with a small build pipeline, not a software project.

## Source rule

- **Edit `book/src/*.md` only.** Chapters are in reading order by filename prefix.
- `book/LP_KDP-Trade_*.md` (the master) is **generated**. `build_kdp.py` rewrites it from `src/` on every run, so edits made to it are lost. A hook blocks direct edits.
- Never edit `book/output/` (build artifacts) or `book/reference/primary/` (public-domain texts that verify the quotations). Hooks block both.
- `book/notes/` (pass report, changelog, incident log, ideas ledger, KDP checklist) is hand-written and safe to edit.

## Commands (run from the repo root)

```bash
python3 book/build/build_kdp.py --master   # reassemble the master from src/ (fast, stdlib only)
python3 book/build/audit_book.py           # citation sweep + quotation audit; exits 1 on failure
python3 book/build/build_kdp.py            # full interior PDF + layout checks (needs TeX; see below)
python3 book/build/build_cover.py          # covers (needs PyMuPDF and the interior PDF's page count)
```

A PostToolUse hook runs the first two after every edit to `book/src/`, `index_terms.py` or `audit_book.py`. A SessionStart hook installs XeLaTeX, makeindex, the fonts and PyMuPDF in cloud sessions. Locally you need pandoc, XeLaTeX (TeX Live), makeindex, TeX Gyre Pagella, DejaVu Serif and PyMuPDF.

## Conventions

- **† and ‡ mark unverified items.** The build strips them from the body above `<!-- MARKS-KEPT-BELOW -->` and keeps them in the appendix. Never delete that marker; `build_kdp.py` refuses to build without it.
- **A quotation without † must be word-for-word in a primary text.** Add each new one to `VERIFIED_QUOTATIONS` in `audit_book.py`. The audit checks every listed fragment against the primary texts **and against the master**, so changing or removing a listed quotation in `src/` fails it. **Known gap:** a quotation you do not list is never checked; list it, or re-check by hand (or with `quotation-integrity`).
- **Citations are APA 7.** The sweep fails on an in-text citation with no Works Cited entry (including an author with no entry at all) and on an entry that is never cited. It reads both "Surname, I. (Year)" and "Name. (Year)." entries. **Known limit:** a citation is recognised only in APA form ("Name, 2001" or "Name (2001)"); a name and year written any other way is invisible to it.
- New index terms go in `book/build/index_terms.py`. Title, author, trim, margins and the master's dated name live only in `book/build/book_config.py`.
- **Weaknesses go in `book/notes/`, not in the book.** An objection enters the text only once a strengthening has been found. Appendix D is the one place the book states its limits.
- Log each correction in `notes/CHANGELOG.md` with the error it replaces, and each problem in `notes/INCIDENT-LOG.md`.

## Skills to use for the next-pass queue

| Task | Skill |
|---|---|
| Reader stress test on the final proof | `document-reader-stress-test` |
| Retraction and editorial-notice check on every DOI | `citation-verification` (Scite `editorialNotices`) |
| Construct-overlap audit, Proposition 10 | `construct-overlap-audit` |
| Find missing sources (trust series, polarisation, elicitation dispersion) | `literature-access`, `literature-review` |
| Attack the recorded weaknesses | `adversarial-pass` |
| Check verbatim quotations | `quotation-integrity` |
| EPUB or another KDP build | `self-published-book-pass` |
| Pre-upload gate | `publication-release-gate` |

## Open items

- `TODO(author)`: the 26 Sep 2026 "standing rulings" are cited in `notes/` (KDP rules checked as of that date; "weaknesses in notes, claims stated plainly in the book") but their text is not in this repo. Add it here so it is not re-derived each pass.
- `TODO(author)`: British or American spelling (pass report, author decision 4). The text is currently British-leaning, while `header.tex` sets American hyphenation.
- Before upload: replace the placeholders for author name, ISBN, author bio and the personal paragraph (`notes/KDP-UPLOAD-CHECKLIST.md`).
