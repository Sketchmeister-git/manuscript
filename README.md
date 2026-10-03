# manuscript

Draft philosophical manuscript: **_The Lion's Problem: Refusal, Anonymous Authority, and the Capacity to Build_**, prepared as a Kindle Direct Publishing (KDP) paperback.

| Path | What it is |
|---|---|
| `book/LP_KDP-Trade_v1.0_Revised-Draft_2026-10-03.md` | **Master manuscript** (source of record; assembled from `book/src/`) |
| `book/src/` | Chapter sources, in reading order (front matter → parts I–IV → conclusion → back matter) |
| `book/output/` | KDP interior PDF (6 × 9 in), paperback wrap cover, front cover, eBook cover JPEG |
| `book/build/` | Build pipeline: `build_kdp.py` (interior), `build_cover.py` (covers), `audit_book.py` (citation and quotation audits), `book_config.py` (title, author, trim and margins) |
| `book/notes/` | Pass report (the five-level edit, weaknesses, author decisions), changelog of corrections, incident log, ideas ledger, KDP upload checklist |
| `book/reference/primary/` | Public-domain primary texts used to verify quotations |

## Rebuild

Requires pandoc, XeLaTeX (TeX Live), makeindex, TeX Gyre Pagella and PyMuPDF.

```bash
cd book/build
python3 build_kdp.py && python3 audit_book.py && python3 build_cover.py
```
