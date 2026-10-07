# Incident Log

Tally (this pass): 9 incidents; 7 resolved in-session, 2 open.

| # | Date | Step | Incident | Resolution |
|---|---|---|---|---|
| 1 | 2026-10-03 | Intake | The 13 attached files were Windows paths (`C:\Users\…`) and did not reach the cloud container. `/mnt/user-data/uploads` was empty. | Located the same files in the author's Google Drive (folder `1flHPS6SV3b06yurPZe63ZF6IatrMQ7hv`, the newest complete set including `04-edition-decision.md`) and read them through the Drive connector. |
| 2 | 2026-10-03 | Intake | The requested `/small-business:report-builder` skill is not installed in this session. | Used `self-published-book-pass`, which covers KDP book builds. |
| 3 | 2026-10-03 | Intake | Drive read of the *Path to Renewal* PDF exceeded the tool-result limit (359,811 characters, mostly reference URLs). | Saved to file and parsed with `jq`; the essay body and reference list were read separately. |
| 4 | 2026-10-03 | Orient | The skill's Step 0 files (`claude/PICK-UP-HERE.md`, work-order ledgers, `40_logs\…`) do not exist in this repository. | Proceeded in Economy mode. State is saved in `book/notes/` in this repo instead. **Open:** mirror these notes to the canonical `40_logs` on the author's drive. |
| 5 | 2026-10-03 | Build | Pandoc, XeLaTeX and PyMuPDF were not preinstalled. | Installed with apt and pip (pandoc 3.x, TeX Live 2023 XeLaTeX, fonts-texgyre, pymupdf). |
| 6 | 2026-10-03 | Build | Pandoc's template issues `\mainmatter` after `-B`, which numbered the Message and Preface in arabic numerals. | `frontmatter.tex` saves `\mainmatter` as `\realmainmatter` and disables the template's call; the Introduction source invokes it. |
| 7 | 2026-10-03 | Build | Chapters were unnumbered and "Conclusion" appeared twice in the contents. | Added `--number-sections` with `secnumdepth=0`, and removed the `\part*{Conclusion}`. |
| 8 | 2026-10-03 | Build | The index came out empty: the fence tracker in `build_kdp.py` started outside a raw-LaTeX fence that was actually open. | Fence state is now carried from the text before `\realmainmatter`. 299 markers, 207-line index. |
| 9 | 2026-10-03 | Verify | The Firecrawl connector reports a low credit balance. | **Open:** top up before the next web-verification pass. |
| 10 | 2026-10-06 | Request | The `/portfolio-build-kickoff` skill (for building web apps) was invoked with the author's answers to the six decisions. It does not apply to a book. | Treated the arguments as the answers to the pass report's decisions 1–6 and applied them. |
| 11 | 2026-10-06 | Spelling | The first conversion pass missed *behaviourally* and *behaviourist* (suffix forms outside the word list). | Caught by a leftover-forms scan; fixed by hand. Re-run the scan after any new text is added. |
| 12 | 2026-10-07 | Adversarial pass | The skill says to put the critique block at the end of the draft; the author's standing ruling of 26 September (critique in an appendix or notes, body confident) conflicts. | Followed the ruling: the block is in `ADVERSARIAL-PASS_2026-10-07.md` and its public subset in Appendix D. Proposed skill update: when ruling 3 is in force, place the block in the notes. |
| 13 | 2026-10-07 | Sources | Hosts hhs.gov (Surgeon General advisory) returned 403; Pew's 2022 social-media page 404. | Used only the verified Pew 2024 teen report; the Surgeon General advisory was not cited. |
