from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sort_by_id_desc(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: safe_int(record.get("id"), -1),
        reverse=True,
    )


def drop_error(errors: list[dict[str, Any]], issue_id: int) -> list[dict[str, Any]]:
    return [error for error in errors if safe_int(error.get("id"), -1) != issue_id]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def load_resume_records(checkpoint_path: Path) -> list[dict[str, Any]]:
    loaded = read_json(checkpoint_path, [])

    if not isinstance(loaded, list):
        return []

    return [item for item in loaded if isinstance(item, dict)]
