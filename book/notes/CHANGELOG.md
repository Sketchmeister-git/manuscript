# Changelog: *The Lion's Problem*

## Build tooling: `audit_book.py` blind spots closed (2026-10-06)

No manuscript text changed. The audit now fails where it used to pass silently:

| # | Audit | What it missed | Now |
|---|---|---|---|
| 1 | Citation sweep | An author cited in the text whose Works Cited entry was missing entirely. The sweep dropped every in-text citation whose author had no entry, so deleting Libet's only entry still reported success. | Every in-text citation is checked; a missing entry is reported as "cited but not in Works Cited". |
| 2 | Citation sweep | Three entries (Aristotle, Laozi, Center for Near-Earth Object Studies) were never parsed, because they are written "Name. (Year)." rather than "Surname, I. (Year)". They were checked in neither direction. | All 56 entries are read. The earlier count of 53 (pass report §7, "53/53") left these three out. |
| 3 | Quotation audit | Quotations as printed in the book. It compared a hand-kept list with the primary texts and never read the master, so a quotation changed in `book/src/` still passed. | Each listed fragment must also appear in the master, in inline, blockquote or italic form, with or without a † mark. |
| 4 | Quotation audit | A listed fragment ("But tell me, my brethren, what the child can do…") was reported as not printed in the book. | False positive: it is the epigraph, printed from `book/build/frontmatter.tex`, not from `book/src/`. The audit now includes the front-matter template in the printed text; the acknowledgement was removed. |

Also: `build_kdp.py` now imports `pymupdf` instead of the deprecated `fitz` name. Not done: listing quotations that are in the book but not in the audit list (the Proposition blockquotes make any heuristic too noisy).

## v1.0 KDP trade edition, revised draft (2026-10-03)

Derived from the modular edition (Modules A–I) and *The Path to Renewal*. Structural changes are documented in `PASS-REPORT_2026-10-03.md`. Corrections, each with the error it replaces:

| # | Location | Error in the source | Correction |
|---|---|---|---|
| 1 | Ch. 4 (Module E) | *Décadence* formulation treated as unverified and unlocated. | Located and quoted verbatim: *Twilight of the Idols* (Ludovici 1911), "Morality as the Enemy of Nature" §2 and "Things the Germans Lack" §6. |
| 2 | Ch. 2 (Module C) | Tocqueville placed in quotation marks: "does not break wills; it softens them, bends them, and directs them". This matches no translation checked. | Now a paraphrase of Reeve ("The will of man is not shattered, but softened, bent, and guided"), cited to Vol. 2, Book 4, Ch. 6. |
| 3 | Ch. 2 (Module B) | The child passage paraphrased in Kaufmann's wording ("self-propelled wheel … sacred Yes") while citing Del Caro. | Quoted verbatim from Common (1909), with Kaufmann's familiar phrase noted. |
| 4 | Ch. 1 (Module A) | NEO figures out of date (18,000 catalogued; 40 per week). | JPL SBDB query, 3 Oct 2026: 42,758 NEOs. Sentry: no object above Torino 0. |
| 5 | Ch. 9 (Module I) | The muddy-water image attributed to Watts without a location. | Attributed to *Tao Te Ching* ch. 15 (Lau translation), the older source Watts drew on. |
| 6 | Apparatus | Libet et al. (1983) listed as having no DOI. | DOI 10.1093/brain/106.3.623, resolved via Crossref. |
| 7 | Apparatus | Group narcissism sourced to *Escape from Freedom* / *Anatomy*. | Cited to *The Heart of Man* (1964), where Fromm develops it. |
| 8 | *Path to Renewal* | "New Senserity". | Not carried forward. The movement is usually called the New Sincerity. |
| 9 | *Path to Renewal* | "Single-entendre" style attributed to Samuel Johnson. | Not carried forward; unsupported. |
| 10 | Apparatus | Project Gutenberg's catalogue credits *The Joyful Wisdom* to Paul V. Cohn. | The title page gives Thomas Common as translator (Cohn and Petre did the poems). The Works Cited follows the title page. |
| 11 | Module I | A "note on the Buber material" referred to Buber passages that the module body does not contain. | Note removed. Buber is not cited in this edition (the edition decision is preserved in the modular edition). |
| 12 | Module C | "Mine mostly fail it, and I have written two books using the term." This is an unverifiable personal claim. | Generalised to "including the uses of people who write about it for a living." **Author: restore the personal version if it is accurate.** |
