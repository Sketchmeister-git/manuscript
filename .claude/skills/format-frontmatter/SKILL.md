---
name: format-frontmatter
description: Audit or add the standard YAML frontmatter, with ISO 8601 timestamps, to markdown files in 10_projects/. Uses scripts/validate-corpus.js as the audit and repairs only what is missing or invalid. Use when asked to check, add, fix, or standardize frontmatter on manuscript drafts.
---

# Format Frontmatter

Bring every markdown file under `10_projects/` into line with the frontmatter standard in `CLAUDE.md` ("File Naming & Frontmatter Standards"). Scope is `10_projects/**/*.md` only.

## Procedure

1. **Audit.** Run from the workspace root:

   ```
   node scripts/validate-corpus.js --json
   ```

   Report the failing files and their issues. If the request was only to audit or check, stop here.
2. **Repair each failing file** (only when asked to fix or add):
   - **No frontmatter**: add a block with all eleven keys: `id`, `title`, `volume`, `edition`, `version`, `status`, `created`, `last_modified`, `stratum`, `tags`, `aliases`.
   - **Frontmatter present but invalid or incomplete**: fix only the missing or invalid keys. Never overwrite a valid existing value. Preserve any extra keys.
   - **Body**: leave it byte-for-byte unchanged and keep the file's existing line endings (LF or CRLF).
3. **Where each value comes from** (never guess; if it cannot be inferred, ask once for the whole batch):
   - `title`: first level-1 heading, else the filename stem.
   - `volume`: from the project folder (table below).
   - `edition`: the `FULL`, `CORE`, or `ESSAY` token in the filename per the naming convention.
   - `version`: the `vMAJOR.MINOR` token in the filename.
   - `status`: `Working` unless told otherwise.
   - `stratum`: `Stratum C (Canonical Philosophical Manuscript)`.
   - `tags`: `[manuscript, philosophy, phenomenology, whole-mind-health]`; `aliases`: `[]`.
   - `created`: first git commit time of the file if tracked, else the file's earliest filesystem time, else now.
   - `id`: the file's `created` value, unless an `id` already exists.
   - `last_modified`: now, and only when this run actually changed the file.
4. **Timestamps** are ISO 8601, `YYYY-MM-DDTHH:mm:ss±hh:mm`, using the UTC offset actually in force at that instant. The template in `CLAUDE.md` shows `-05:00` (EST); during daylight time the correct offset is `-04:00`, and the validator accepts both. Get the current value with `date +%Y-%m-%dT%H:%M:%S%:z` or `node -e "console.log(require('./scripts/lib/frontmatter').formatLocalIso8601())"`.
5. **Verify.** Re-run `node scripts/validate-corpus.js`. Report the failing count before and after.
6. **Report** with a differential change log first (per `CLAUDE.md`): for each file, which keys were added or changed, and why.

## Volume mapping (to confirm)

| Project folder | Volume |
|---|---|
| `Nobody_Gave_the_Order` | Vol I |
| `The_Great_Inversion` | Vol II |
| `The_Second_Position` | Vol III |

This mapping follows the order in which the workspace brief lists the works. The author has not confirmed it. Confirm it before the first bulk run, and update this table if it is wrong.
