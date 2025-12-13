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
    owner_pid: int | None
    is_active: bool
    is_focused_window: bool


@dataclass
class WindowDataEntry:
    timestamp: datetime
    focused_app_name: str | None
    focused_app_pid: int | None
    focused_window_name: str | None
    windows: list[WindowInfo]

    @property
    def active_window(self) -> WindowInfo | None:
        focused = next((w for w in self.windows if w.is_focused_window), None)
        if focused is not None:
            return focused

        if self.focused_app_pid is not None:
            by_pid = next(
                (
                    w
                    for w in self.windows
                    if w.owner_pid is not None and w.owner_pid == self.focused_app_pid
                ),
                None,
            )
            if by_pid is not None:
                return by_pid

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
        focused_app_name = obj.get("focused_app_name")
        focused_app_pid = obj.get("focused_app_pid")
        focused_window_name = obj.get("focused_window_name")
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
            owner_pid = w.get("owner_pid")
            is_active = bool(w.get("is_active"))
            is_focused_window = bool(w.get("is_focused_window"))
            if isinstance(app_name, str) and isinstance(window_name, str):
                windows.append(
                    WindowInfo(
                        app_name=app_name,
                        window_name=window_name,
                        owner_pid=owner_pid if isinstance(owner_pid, int) else None,
                        is_active=is_active,
                        is_focused_window=is_focused_window,
                    )
                )

        return WindowDataEntry(
            timestamp=ts,
            focused_app_name=focused_app_name
            if isinstance(focused_app_name, str)
            else None,
            focused_app_pid=focused_app_pid
            if isinstance(focused_app_pid, int)
            else None,
            focused_window_name=focused_window_name
            if isinstance(focused_window_name, str)
            else None,
            windows=windows,
        )

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
