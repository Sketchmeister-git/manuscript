#!/usr/bin/env python3
"""PostToolUse hook: keep the master in sync with src/ and run the mechanical audits.

Claude Code runs this after every Edit or Write and passes the tool call as JSON on
stdin. For edits to the chapter sources (or to the audit and index vocabularies) it:

    1. reassembles the master:   python3 book/build/build_kdp.py --master
    2. runs the audits:          python3 book/build/audit_book.py
                                 (two-way citation sweep and verified-quotation audit)

Both steps need only the Python standard library, so this runs in about a second and
needs no TeX. The hook is silent when everything passes. On failure it prints the
failing tool's own output and exits 2, which sends it to Claude. The edit has already
happened, so this is feedback, not a block.

Expect a "cited but not in Works Cited" report mid-draft if a citation is added before
its Works Cited entry. That is the audit working as intended.

This hook reports exactly what audit_book.py reports, and audit_book.py has two blind
spots (see CLAUDE.md): it does not notice an author whose Works Cited entry is missing
entirely, and it never compares the quotations printed in the book to the primary
texts. A silent pass therefore means "no audit failure", not "every check passed".
"""

import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

BUILD_TIMEOUT_SECONDS = 60

# Files whose edits can change the audit result: chapter sources and the two
# vocabularies the build and the audit read.
WATCHED_BUILD_FILES = {"index_terms.py", "audit_book.py"}


def read_target_path() -> str:
    """Return the file_path of the completed Edit/Write call, or '' if there is none."""
    try:
        tool_call = json.load(sys.stdin)
    except json.JSONDecodeError:
        return ""
    return str(tool_call.get("tool_input", {}).get("file_path", ""))


def project_directory() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def is_watched(file_path: str, project_dir: Path) -> bool:
    """True when the edited file is a chapter source or a watched build file."""
    relative = PurePosixPath(os.path.relpath(os.path.abspath(file_path), project_dir).replace(os.sep, "/"))
    parts = relative.parts
    is_chapter_source = len(parts) == 3 and parts[:2] == ("book", "src") and relative.suffix == ".md"
    is_watched_build_file = len(parts) == 3 and parts[:2] == ("book", "build") and parts[2] in WATCHED_BUILD_FILES
    return is_chapter_source or is_watched_build_file


def run_step(script_path: Path, arguments: list) -> subprocess.CompletedProcess:
    """Run one build script and return the finished process (output captured)."""
    return subprocess.run(
        [sys.executable, str(script_path), *arguments],
        capture_output=True,
        text=True,
        timeout=BUILD_TIMEOUT_SECONDS,
    )


def report_failure(label: str, result: subprocess.CompletedProcess) -> int:
    """Send a failing step's output to Claude and signal exit code 2."""
    details = (result.stdout + result.stderr).strip()
    print(f"{label} failed (exit {result.returncode}):\n{details}", file=sys.stderr)
    return 2


def main() -> int:
    file_path = read_target_path()
    project_dir = project_directory()
    if not file_path or not is_watched(file_path, project_dir):
        return 0

    build_dir = project_dir / "book" / "build"
    try:
        assemble = run_step(build_dir / "build_kdp.py", ["--master"])
        if assemble.returncode != 0:
            return report_failure("Master assembly (build_kdp.py --master)", assemble)
        audit = run_step(build_dir / "audit_book.py", [])
    except subprocess.TimeoutExpired:
        print(f"Audit hook timed out after {BUILD_TIMEOUT_SECONDS}s.", file=sys.stderr)
        return 2
    if audit.returncode != 0:
        return report_failure("Audit (audit_book.py)", audit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
