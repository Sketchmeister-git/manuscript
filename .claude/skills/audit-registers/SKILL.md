---
name: audit-registers
description: Audit a manuscript draft for register conflation. Checks that phenomenological, psychoanalytic, and cognitive/neurobiological claims are rigorously differentiated per the Three-Register Methodological Separation in CLAUDE.md. Use when asked to audit, check, or review a draft's registers, or before finalizing a chapter.
---

# Audit Registers

Inspect one draft for register conflation and report it. Read-only by default.

## Input

A path to a draft (usually under `10_projects/`). If none is given, ask for one. Do not guess.

## Standard being applied

Use the definitions in `CLAUDE.md` under "Three-Register Methodological Separation". In short:

- **Phenomenological**: lived experience structured from within the lifeworld. Descriptive, not explanatory.
- **Psychoanalytic**: unconscious defensive architectures, split ego dynamics, compensatory idolatry (Fromm, Becker). Interpretive.
- **Cognitive / Neurobiological**: predictive processing, sensory gating, brainstem default responses (default passivity, moral distress). Mechanistic.
- **Rule of Transition**: never borrow an adjacent register to lend unearned authority; formulate phenomenological structures before metaphysical abstractions.

## Procedure

1. Read `CLAUDE.md` first, then the draft in full. Skip the frontmatter.
2. Work heading by heading, paragraph by paragraph. Label locations as `<heading> ¶<n>` (paragraph number within that heading).
3. Classify each claim-bearing paragraph as **Phenomenological**, **Psychoanalytic**, **Neurobiological**, **Mixed**, or **Apparatus** (transition, citation, or signpost text with no claim of its own).
4. Flag defects using these codes:
   - **R1 Conflation**: one claim or sentence draws on two registers without marking the shift.
   - **R2 Borrowed authority**: a term from one register certifies a claim in another (for example, a neural mechanism cited to "prove" a described experience).
   - **R3 Explanatory leakage**: causal or mechanistic explanation inside a passage that should be purely descriptive.
   - **R4 Premature abstraction**: a metaphysical abstraction appears before the phenomenological structure that grounds it (Rule of Transition ordering).
   - **R5 Unmarked transition**: the operating register changes between paragraphs or sections with no signpost.
   - **R6 Unsupported mechanism**: a neurobiological or psychoanalytic claim stated as fact with no citation or Knowledge Item. Flag the gap only; never invent a citation.
5. For each flag give: the location, the register operating, the register borrowed (if any), at most 25 words of quoted evidence, and a minimal fix (split the sentence, add a transition marker, reorder, restate as description, or add the claim to a pending-citation list). Do not rewrite for style.

## Output

Use direct, objective prose with no filler (per `CLAUDE.md`).

1. One line: files audited, paragraphs classified, flags raised by code.
2. Table: `| Location | Register(s) | Code | Evidence | Proposed fix |`.
3. Register balance: paragraph counts per register.
4. Up to two exemplars of clean separation, if any exist.

## Editing and saving

- Do not edit the draft unless asked.
- If asked to apply fixes: apply only the approved ones, and prepend the explicit Differential Change Log required by `CLAUDE.md` (sections and paragraphs modified, with the rationale for each) before presenting the edited text.
- Save the audit to `40_logs/change_records/` only on request, as `audit-registers_<draft-stem>_<YYYY-MM-DD>.md`.
