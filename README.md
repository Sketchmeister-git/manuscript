# manuscript
draft philosophical manuscript

## Workspace layout

This repository is the workspace root for the multi-volume manuscript (*Nobody Gave the Order*, *The Great Inversion*, *The Second Position*). Governance rules live in [`CLAUDE.md`](CLAUDE.md).

| Path | Purpose |
|---|---|
| `00_inbox/` | Raw clippings, temporary notes, voice transcripts |
| `10_projects/` | One folder per work: `Nobody_Gave_the_Order`, `The_Great_Inversion`, `The_Second_Position` |
| `20_areas/` | `phenomenology`, `psychoanalysis`, `cognitive_neurobiology` |
| `30_resources/` | `knowledge_items` (tagged citation extracts), `lexicons`, `primary_sources` |
| `40_logs/` | `checkpoints` (session handoff blocks), `change_records` (differential change audit logs) |
| `90_archive/` | Superseded drafts and legacy revisions |
| `scripts/` | Node.js automation (no dependencies, no `npm install`) |
| `.claude/skills/` | Custom Claude Code skills: `audit-registers`, `create-checkpoint`, `format-frontmatter` |

PDFs are git-ignored (`.gitignore` cannot filter by size); markdown, yaml, docx, scripts and skills are tracked.

## Local setup (Windows 11)

1. Clone this repository to `C:\Users\danzy\Local\New Manuscript`.
2. Preview the Claude Desktop MCP changes (writes nothing):

   ```
   node scripts/install-mcp-config.js --dry-run
   ```

3. Apply them. The script backs up `%APPDATA%\Claude\claude_desktop_config.json`, merges only the `mcpServers` entries, and re-verifies the result:

   ```
   node scripts/install-mcp-config.js
   ```

4. Fully quit Claude Desktop from the system tray, relaunch it, and confirm `filesystem`, `memory` and `fetch` under Settings > Developer.

The memory server's data is stored in `40_logs/memory.jsonl` (set through `MEMORY_FILE_PATH`), so it survives npx cache refreshes. That file is git-ignored because it holds private concept notes. If a `memory` entry from an earlier run already exists, re-run with `--force` to update it.

Requirements: Node.js (for `npx`) and [uv](https://docs.astral.sh/uv/) (for `uvx mcp-server-fetch`; the npm package `@modelcontextprotocol/server-fetch` does not exist). The installer warns if either is missing or if an allowed folder does not exist.

## Scripts

| Command | What it does |
|---|---|
| `node scripts/validate-corpus.js` | Checks frontmatter (required keys, ISO 8601 timestamps, version pattern, vocabularies) on every markdown file in `10_projects/`; exits 1 on failure |
| `node scripts/checkpoint.js <draft> --tension "..." --pending "..."` | Writes `40_logs/checkpoints/checkpoint_YYYY-MM-DD_HHmmss.json` for a draft |
| `node scripts/install-mcp-config.js [--dry-run] [--check] [--force]` | Registers the MCP servers in Claude Desktop's config |
