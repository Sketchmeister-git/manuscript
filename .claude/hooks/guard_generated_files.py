#!/usr/bin/env python3
"""PreToolUse guard: stop edits to generated files and to verification ground truth.

Claude Code runs this before every Edit or Write and passes the tool call as JSON
on stdin. Exit code 2 blocks the call and sends our message back to Claude, so the
message says what to do instead. Exit code 0 lets the call through.

Why these paths are protected:

    book/<MASTER_NAME>.md      Regenerated from book/src/*.md on every run of
                               build_kdp.py, so a hand edit is silently lost.
    book/reference/primary/    Public-domain primary texts. audit_book.py checks the
                               verified quotations against them; editing one would
                               quietly corrupt the audit.
    book/output/               PDFs and covers written by the build scripts.
"""

import json
import os
import sys
from pathlib import PurePosixPath
from typing import Optional

MASTER_MESSAGE = (
    "Blocked: {path} is the generated master manuscript. build_kdp.py rewrites it from "
    "book/src/*.md on every run, so edits made here are lost. Edit the matching chapter "
    "in book/src/ instead, then run: python3 book/build/build_kdp.py --master"
)
PRIMARY_TEXT_MESSAGE = (
    "Blocked: {path} is a primary source text used by audit_book.py to verify quotations. "
    "Do not edit it. If a quotation does not match, fix the quotation in book/src/."
)
BUILD_ARTIFACT_MESSAGE = (
    "Blocked: {path} is a build artifact. Regenerate it with the scripts in book/build/ "
    "instead of editing it."
)


def read_target_path() -> str:
    """Return the file_path of the pending Edit/Write call, or '' if there is none."""
    try:
        tool_call = json.load(sys.stdin)
    except json.JSONDecodeError:
        return ""
    return str(tool_call.get("tool_input", {}).get("file_path", ""))


def path_relative_to_project(file_path: str) -> PurePosixPath:
    """Express file_path relative to the project root, with forward slashes."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, os.path.abspath(project_dir))
    return PurePosixPath(relative_path.replace(os.sep, "/"))


def blocking_message(relative_path: PurePosixPath) -> Optional[str]:
    """Return the reason this path is protected, or None if edits are allowed."""
    parts = relative_path.parts
    is_master = len(parts) == 2 and parts[0] == "book" and relative_path.suffix == ".md"
    if is_master:
        return MASTER_MESSAGE.format(path=relative_path)
    if parts[:3] == ("book", "reference", "primary"):
        return PRIMARY_TEXT_MESSAGE.format(path=relative_path)
    if parts[:2] == ("book", "output"):
        return BUILD_ARTIFACT_MESSAGE.format(path=relative_path)
    return None


def main() -> int:
    file_path = read_target_path()
    if not file_path:
        return 0
    message = blocking_message(path_relative_to_project(file_path))
    if message is None:
        return 0
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
