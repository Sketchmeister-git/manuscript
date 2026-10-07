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

## Author rulings applied, 2026-10-06

| # | Change | Detail |
|---|---|---|
| 13 | Author and ISBN | Author: Brian Danzyger (title page, copyright page, running heads, cover, Message sign-off). ISBN set to the placeholder `xxx-xxx-xxxxx`. |
| 14 | Subtitle | *From Refusal to Authorship* (was *Refusal, Anonymous Authority, and the Capacity to Build*). |
| 15 | American spelling | 160 replacements across `book/src/` from an explicit word list (behavior, optimized, civilization, defense, modeling, organize, armor, sidewalk, program and others), plus: *petrol pump* to *gas pump*, *lift* to *elevator*, *queue* to *checkout line*, and the date "3 October 2026" to "October 3, 2026". Not changed: verbatim quotations (Jung's "saviour" in Chapter 8 and Appendix E) and the Works Cited. The audit confirms all 14 verified quotations and all 56 references are unaffected. |
| 16 | New formats | `build/build_formats.py` builds the EPUB 3 and Word editions from the master. Parts and chapter numbers are written into the headings, the front matter is generated from `book_config.py`, and the † ‡ marks appear only in Appendix E. |
| 17 | Paper stock | Kept cream; the wrap cover, spine (0.3825 in at 153 pp.) and interior are built from the same page count, so they agree. |
| 18 | Kept as placeholders (author's choice) | The personal paragraph and city in *A Message from the Author*, and the back-cover bio. |

## Source pass, 2026-10-06 (continuing the next-pass queue)

| # | Where | Gap or error | Resolution |
|---|---|---|---|
| 19 | Ch. 1; Appendix C | Expert dispersion on unprecedented risks was asserted with no source. | Added Karger et al. (2023): median extinction by 2100 of 6% (domain experts) vs 1% (superforecasters); AI-caused extinction 3% vs 0.38%; the report's table of published AI-extinction estimates spans 25% to 0.38% (about sixtyfold, with differing definitions and horizons). Figures read from the report's Tables 1 and 6. |
| 20 | Ch. 3; Appendix C | "Long-running survey series … show declines across nearly every category they track" was unsupported as stated. | Replaced with what the source shows: Brenan (2025), Gallup's nine institutions average 28%, near the 46-year low, under 30% four years running; the party gap (37% vs 26%) is the series maximum and moves with control of the presidency. The category-by-category claim is no longer made. |
| 21 | Ch. 9; Appendix C, D | The claim that civil conflict is the threat within a citizen's reach had no citation either way. | Added Iyengar et al. (2019) and Voelkel et al. (2024) with an explicit statement of what they do and do not show (attitudes in an experiment; treatments, not norms). Logged as a weak joint in Appendix D. |
| 22 | Works Cited | Four sources added (Brenan; Iyengar et al.; Karger et al.; Voelkel et al.). | 60 entries; the citation sweep matches 60/60 in both directions. |
| 23 | Retraction check | No retraction or editorial-notice check had been run. | All 25 DOIs in the Works Cited, and the two new ones, return no `updated-by` notices from Crossref (which includes the Retraction Watch records). Not a substitute for each publisher's own page. |

## Proposition 10 audit and reader test, 2026-10-06

| # | Where | Change |
|---|---|---|
| 24 | Ch. 8, Proposition 10, Appendices B–D | The audit of "same capacity" found a family of related tolerances, not one faculty (Wesner et al., 2023; Hsu et al., 2023: behavioral and self-report indicators did not form one dimension). Proposition 10 now claims a shared ingredient and one family of capacities, and a new section, "One capacity, or a family of them?", gives the evidence. Kapur (2015) and Darabi et al. (2018) added for the incompetence phase. Four Works Cited entries (64 total). Appendix D now lists a transfer test. |
| 25 | Whole book | Reader-test fixes: see `READER-TEST_2026-10-06.md` for the full table (about 30 changes). |
| 26 | Ch. 1; Appendix E | The 1998 NASA survey goal is reworded and marked † because its source and completion were not confirmed. |

## Adversarial pass, 2026-10-07

| # | Where | Change |
|---|---|---|
| 27 | Ch. 7; Works Cited; Appendices C, D | One measured case added for "assent has changed almost nothing": Pew (2024), nearly half of US teens online almost constantly, up from 24% a decade earlier. Scope stated (teens, self-report). |
| 28 | Ch. 3 | Gallup's independents (25%, level for three years) identified as the lion's signature; the partisans' swings assigned to group loyalty, with the lion diagnosis said not to explain them. |
| 29 | Ch. 6; Works Cited; Appendices C, E | Popper (1945/1966) and Whitson and Galinsky (2008) credited as the nearest existing constructs. Popper's paraphrase is marked ‡ and needs a page locator. |
| 30 | Notes | `ADVERSARIAL-PASS_2026-10-07.md` added: four questions, four aporias, the critic-in-corpus choice, falsification conditions. |
