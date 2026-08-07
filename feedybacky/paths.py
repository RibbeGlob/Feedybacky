from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPaths:
    output_dir: Path
    processed_dir: Path
    raw_dir: Path
    list_checkpoint: Path
    list_progress: Path
    tickets_checkpoint: Path
    comments_checkpoint: Path
    errors: Path
    tickets: Path
    comments: Path

    @classmethod
    def from_output_dir(cls, output_dir: Path) -> "ExportPaths":
        processed_dir = output_dir / "processed"
        return cls(
            output_dir=output_dir,
            processed_dir=processed_dir,
            raw_dir=output_dir / "raw_sanitized",
            list_checkpoint=output_dir / "issue_list_checkpoint2.json",
            list_progress=output_dir / "issue_list_progress2.json",
            tickets_checkpoint=output_dir / "tickets_checkpoint2.json",
            comments_checkpoint=output_dir / "comments_checkpoint2.json",
            errors=output_dir / "errors.json",
            tickets=processed_dir / "tickets.json",
            comments=processed_dir / "comments.json",
        )

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
