# CLAUDE.md — Manuscript Development & Operational Architecture

## Core Directives & Style
1. **Objective Stance**: Maintain an intellectually rigorous, non-apologetic, and direct tone. Never use conversational filler, hollow moralizing, or unearned superlatives.
2. **Differential Change Accounting**: When editing any chapter, draft, or outline, always prepend the output with an explicit change log detailing:
   - Specific sections and paragraphs modified.
   - Conceptual, theoretical, or stylistic rationale for each adjustment.
3. **Three-Register Methodological Separation**:
   - *Phenomenological*: Lived experience structured from within the lifeworld (descriptive, not explanatory).
   - *Psychoanalytic*: Unconscious defensive architectures, split ego dynamics, and compensatory idolatry (Fromm, Becker).
   - *Cognitive / Neurobiological*: Predictive processing, sensory gating, brainstem default responses (default passivity, moral distress).
   - *Rule of Transition*: Never borrow an adjacent register to lend unearned authority. Formulate phenomenological structures prior to metaphysical abstractions.

## Token Optimization & Context Stewardship
- **200k Token Lifecycle**:
  - `0k - 60k`: Prime drafting and deep dialectical synthesis.
  - `60k - 120k`: Active section drafting.
  - `120k - 160k`: Conclude chapter sprint; avoid importing new reference books.
  - `> 160k`: Mandatory checkpoint execution and session restart.
- **Reference Ingestion**: Ingest targeted Knowledge Items (tagged quotes with page citations) rather than whole PDFs.
- **Session Scoping**: Limit working chat context to 1–2 chapters at a time.

## File Naming & Frontmatter Standards
- Naming Convention: `[Project]_[Edition]_[Version]_[Descriptor]_[YYYY-MM-DD].[ext]`
  - Editions: `FULL` (Working treatise), `CORE` (Academic monograph), `ESSAY` (Platform/trade condensation).
- Mandatory YAML Frontmatter on all notes and drafts:
  ```yaml
  ---
  id: "YYYY-MM-DDTHH:mm:ss-05:00"
  title: "Chapter or Note Title"
  volume: "Vol I | Vol II | Vol III"
  edition: "FULL | CORE | ESSAY"
  version: "v4.0"
  status: "Working | Superseded | Canonical"
  created: "YYYY-MM-DDTHH:mm:ss-05:00"
  last_modified: "YYYY-MM-DDTHH:mm:ss-05:00"
  stratum: "Stratum C (Canonical Philosophical Manuscript)"
  tags: [manuscript, philosophy, phenomenology, whole-mind-health]
  aliases: []
  ---
  ```
