from __future__ import annotations

from pathlib import Path

MAX_OUTPUT_CHARS = 50_000


def current_workspace() -> Path:
    return Path.cwd().resolve()


def resolve_workspace_path(path_str: str) -> Path:
    normalized_path = path_str.strip()
    if not normalized_path:
        raise ValueError("Path must not be empty")

    workspace = current_workspace()
    raw_path = Path(normalized_path)
    candidate = raw_path if raw_path.is_absolute() else workspace / raw_path
    resolved = candidate.resolve()

    if not resolved.is_relative_to(workspace):
        raise ValueError(f"Path escapes workspace: {path_str}")

    return resolved


def truncate_text(text: str, *, max_chars: int = MAX_OUTPUT_CHARS) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True
