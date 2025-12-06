from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging


@dataclass
class WindowInfo:
    app_name: str
    window_name: str
    is_active: bool


@dataclass
class WindowDataEntry:
    timestamp: datetime
    windows: list[WindowInfo]

    @property
    def active_window(self) -> WindowInfo | None:
        return next((w for w in self.windows if w.is_active), None)


class WindowDataParser:
    def parse_file(self, file_path: Path) -> list[WindowDataEntry]:
        entries: list[WindowDataEntry] = []
        if not file_path.exists() or not file_path.is_file():
            return entries
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    entry = self.parse_line(line)
                    if entry is not None:
                        entries.append(entry)
        except PermissionError as e:
            logging.error("Permission error reading window data: %s", e)
            return []
        except OSError as e:
            logging.error("OS error reading window data: %s", e)
            return []
        return entries

    def parse_line(self, line: str) -> WindowDataEntry | None:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            logging.warning("Malformed JSON line in window data")
            return None
        ts_str = obj.get("timestamp")
        windows_raw = obj.get("windows", [])
        if not ts_str or not isinstance(windows_raw, list):
            logging.warning("Invalid window data entry structure")
            return None
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            logging.warning("Invalid timestamp in window data entry")
            return None
        windows: list[WindowInfo] = []
        for w in windows_raw:
            app_name = w.get("app_name")
            window_name = w.get("window_name")
            is_active = bool(w.get("is_active"))
            if isinstance(app_name, str) and isinstance(window_name, str):
                windows.append(
                    WindowInfo(
                        app_name=app_name, window_name=window_name, is_active=is_active
                    )
                )
        return WindowDataEntry(timestamp=ts, windows=windows)

    def match_timestamp_to_video_position(
        self,
        timestamp: datetime,
        video_start: datetime,
        video_duration_ms: int,
    ) -> int:
        delta_ms = int((timestamp - video_start).total_seconds() * 1000)
        if delta_ms < 0:
            return 0
        if delta_ms > video_duration_ms:
            return video_duration_ms
        return delta_ms
