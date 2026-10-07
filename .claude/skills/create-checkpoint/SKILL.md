---
name: create-checkpoint
description: Create a standardized Checkpoint Block for a manuscript draft in 40_logs/checkpoints/ so a session can be handed off or restarted. Records working title, edition, semantic version, last completed section and word count, active thematic tension, pending primary source citations, and destination file path. Use when asked to checkpoint or save state, when context passes about 160k tokens, or before ending a session.
---

# Create Checkpoint

Produce a session-handoff record for one draft: a machine record (JSON, written by `scripts/checkpoint.js`) and a readable Checkpoint Block (Markdown, same filename stem).

## Input

A draft path. If none is given, ask. Do not guess.

## Procedure

1. **Collect what the script cannot compute.**
   - **Active thematic tension / unresolved aporia**: one or two sentences naming both poles of the tension as it stands at the end of this session. If it is not clear from the session, ask.
   - **Pending primary source citations**: every claim that still needs a source, as author, work, and page where known. One entry per claim. Never invent a citation; an unknown page stays unknown.
   - **Last completed section**: the script defaults to the last heading in the draft. If that heading is not the last *completed* section, pass `--last-section`.
   - **Destination file path**: where the next session resumes. It defaults to the draft itself; pass `--destination` if the work continues elsewhere.
2. **Run the script** from the workspace root:

   ```
   node scripts/checkpoint.js "<draft>" --tension "<text>" --pending "<citation 1>" --pending "<citation 2>" [--last-section "<heading>"] [--destination "<path>"]
   ```

   It writes `40_logs/checkpoints/checkpoint_YYYY-MM-DD_HHmmss.json`. If it exits non-zero, report the error as printed and stop.
3. **Render the Checkpoint Block** beside the JSON, as `checkpoint_YYYY-MM-DD_HHmmss.md`, filled from the JSON values (do not recompute or retype them):

   ```
   # Checkpoint: <working_title>

   - Created: <created_at>
   - Edition: <edition>
   - Semantic version: <semantic_version>
   - Last completed section: <last_completed_section> (<word_count> words in draft; <last_section_word_count> in that section)
   - Active thematic tension / unresolved aporia: <active_thematic_tension>
   - Pending primary source citations:
     - <each entry>
   - Destination file path: <destination_file_path>
   - Source integrity: sha256 <source.sha256>
   - Warnings: <warnings, or "none">
   ```
4. **Report** the two file paths and one line stating where the next session resumes.

## Handoff discipline

Per `CLAUDE.md`, the next session loads this checkpoint and the destination file only, and works on one or two chapters at a time. Past 160k tokens a checkpoint and restart are mandatory.
