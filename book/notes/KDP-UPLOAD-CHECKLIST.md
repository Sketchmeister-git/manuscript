# KDP Upload Checklist: Paperback

Rules checked against KDP guidance as of 26 Sep 2026 (per the standing ruling). **Re-check at kdp.amazon.com before uploading.**

| Item | Status | Value / file |
|---|---|---|
| Trim size | ✅ | 6 × 9 in, no bleed (interior) |
| Interior PDF | ✅ | `output/LP_KDP-Trade_v1.0_Revised-Draft_2026-10-03_KDP-Interior.pdf` (163 pp.) |
| Margins | ✅ | inner 0.75 in (KDP minimum is 0.375 in up to 150 pp. and 0.5 in up to 300 pp.); outer 0.6 in (minimum 0.25 in) |
| Fonts embedded | ✅ | `pdffonts`: all embedded (interior and cover) |
| Missing glyphs | ✅ | none in the XeLaTeX log |
| Overfull lines > 10 pt | ✅ | 0 |
| Blank pages | ✅ | only openright versos (KDP allows these) |
| Cover wrap | ✅ | `output/…_Cover-Paperback-Wrap.pdf`, 12.658 × 9.250 in (cream paper; 0.125 in bleed; spine 0.4075 in) |
| Spine text | ✅ | Allowed (≥ 79 pp.) |
| Barcode area | ✅ | 2 × 1.2 in clear white box, back panel, bottom right |
| eBook cover | ✅ | `output/…_Cover-eBook.jpg`, 1600 × 2400 px |
| Author name | ✅ | Brian Danzyger (`build/book_config.py`) |
| **ISBN** | ❌ | placeholder `xxx-xxx-xxxxx` (`ISBN_PAPERBACK`); KDP wants a 13-digit ISBN or its free one, so replace it before upload |
| **Author bio** | ❌ | placeholder on the back cover (`build/build_cover.py`) |
| **Personal paragraph and city** | ❌ | placeholders in *A Message from the Author* (`src/01-message.md`), kept at the author's direction for now |
| Kindle eBook | ✅ | `output/…​.epub` (cover, contents, parts and chapters; no page-number index) |
| Word manuscript | ✅ | `output/…​.docx` |
| Paper colour matches the cover | ⚠️ | cover built for **cream**; if you choose white, set `PAPER = "white"` and rebuild |
| AI-content disclosure at upload | ⚠️ | author decision |
| Book description | ⚠️ | draft from *The Argument in Brief* and the back-cover blurb |
| Categories and keywords | ⚠️ | suggested: Philosophy › Political; Psychology › Social Psychology; Social Science › Media Studies. Keywords: anonymous authority, attention economy, conspiracy theories psychology, Nietzsche lion, moral distress, digital civics, Erich Fromm |

## Rebuild

```bash
cd book/build
python3 build_kdp.py      # interior PDF + checks
python3 audit_book.py     # citation sweep + quotation audit (exit 1 on failure)
python3 build_cover.py    # wrap, front and eBook covers (needs the interior page count)
python3 build_formats.py  # EPUB and Word
```
