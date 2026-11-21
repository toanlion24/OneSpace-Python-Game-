"""Player progress: completed levels and the code written for each level.

Saved in two places so a student does not lose work:
  1. the main file   %APPDATA%/OneSpaceCodeQuest/progress.json  (kept when the game is re-installed)
  2. a backup copy   Documents/OneSpace CodeQuest/tien-do.json  (easy to find and copy to a USB stick)
Writes are atomic (temp file + replace) and the previous main file is kept as progress.json.bak.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

FORMAT_VERSION = 1
BACKUP_NAME = "tien-do.json"


def _read(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


class Progress:
    def __init__(self, main_file: Path, backup_dir: Path | None = None) -> None:
        self.main_file = main_file
        self.backup_dir = backup_dir
        self.completed: set[str] = set()
        self.code: dict[str, str] = {}
        self.restored_from_backup = False
        self._load()

    # ------------------------------------------------------------ loading
    @property
    def backup_file(self) -> Path | None:
        return self.backup_dir / BACKUP_NAME if self.backup_dir else None

    def _load(self) -> None:
        data = _read(self.main_file)
        if data is None:
            data = _read(self.main_file.with_name(self.main_file.name + ".bak"))
        if data is None and self.backup_file is not None:
            data = _read(self.backup_file)
            self.restored_from_backup = data is not None and bool(data.get("completed") or data.get("code"))
        if data is not None:
            self._merge(data)

    def _merge(self, data: dict[str, Any]) -> int:
        """Merge saved data into this progress. Returns how many new completed levels were added."""
        before = len(self.completed)
        self.completed |= {str(level_id) for level_id in data.get("completed", [])}
        for level_id, text in dict(data.get("code", {})).items():
            if isinstance(text, str) and level_id not in self.code:
                self.code[str(level_id)] = text
        return len(self.completed) - before

    # ------------------------------------------------------------ saving
    def to_json(self) -> str:
        data = {
            "app": "OneSpace CodeQuest",
            "format": FORMAT_VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "completed": sorted(self.completed),
            "code": self.code,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def save(self) -> None:
        text = self.to_json()
        if self.main_file.exists():
            try:
                os.replace(self.main_file, self.main_file.with_name(self.main_file.name + ".bak"))
            except OSError:
                pass
        _write_atomic(self.main_file, text)
        if self.backup_file is not None:
            try:
                _write_atomic(self.backup_file, text)
            except OSError:
                pass

    def export_backup(self) -> Path | None:
        """Write the backup copy now. Returns its path, or None if there is no backup folder."""
        if self.backup_file is None:
            return None
        _write_atomic(self.backup_file, self.to_json())
        return self.backup_file

    def restore_backup(self) -> int | None:
        """Merge the backup copy into current progress. Returns new completed levels, or None if no backup."""
        if self.backup_file is None:
            return None
        data = _read(self.backup_file)
        if data is None:
            return None
        added = self._merge(data)
        self.save()
        return added
