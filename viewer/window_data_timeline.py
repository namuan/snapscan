from __future__ import annotations
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from .window_data_parser import WindowDataEntry, WindowDataParser
from .video_player import VideoPlayerWidget


class WindowDataTimeline(QWidget):
    def __init__(self):
        super().__init__()
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Time", "App", "Window"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setShowGrid(False)
        lay = QVBoxLayout()
        lay.addWidget(self._table)
        self.setLayout(lay)
        self._entries: list[WindowDataEntry] = []
        self._entry_positions: list[int] = []
        self._video_start: datetime | None = None
        self._video_duration_ms: int = 0

    def load_window_data(self, entries: list[WindowDataEntry]):
        self._entries = sorted(entries, key=lambda e: e.timestamp)
        self._table.setRowCount(len(self._entries))
        for i, e in enumerate(self._entries):
            t_item = QTableWidgetItem(e.timestamp.strftime("%H:%M:%S"))
            aw = e.active_window
            app = aw.app_name if aw else ""
            win = aw.window_name if aw else ""
            app_item = QTableWidgetItem(app)
            win_item = QTableWidgetItem(win)
            for it in (t_item, app_item, win_item):
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(i, 0, t_item)
            self._table.setItem(i, 1, app_item)
            self._table.setItem(i, 2, win_item)
        if self._video_start is not None:
            self._recompute_positions()

    def update_current_position(self, video_position_ms: int):
        if not self._entries or not self._video_start:
            return
        if not self._entry_positions or len(self._entry_positions) != len(
            self._entries
        ):
            self._recompute_positions()
        idx = self._find_index_for_position(video_position_ms)
        if idx is None:
            return
        self._table.selectRow(idx)
        self._table.scrollToItem(self._table.item(idx, 0))

    def clear(self):
        self._entries = []
        self._entry_positions = []
        self._table.setRowCount(0)
        self._video_start = None
        self._video_duration_ms = 0

    def set_video_timing(self, video_start: datetime, video_duration_ms: int):
        self._video_start = video_start
        self._video_duration_ms = max(0, int(video_duration_ms))
        if self._entries:
            self._recompute_positions()

    def bind_to_player(self, player: VideoPlayerWidget, video_start: datetime):
        self.set_video_timing(video_start, player.get_duration())
        player.position_changed.connect(self.update_current_position)

    def _recompute_positions(self):
        parser = WindowDataParser()
        self._entry_positions = [
            parser.match_timestamp_to_video_position(
                e.timestamp, self._video_start, self._video_duration_ms
            )
            for e in self._entries
        ]

    def _find_index_for_position(self, pos_ms: int) -> int | None:
        if not self._entry_positions:
            return None
        lo, hi = 0, len(self._entry_positions) - 1
        if pos_ms <= self._entry_positions[0]:
            return 0
        if pos_ms >= self._entry_positions[hi]:
            return hi
        while lo <= hi:
            mid = (lo + hi) // 2
            cur = self._entry_positions[mid]
            if cur == pos_ms:
                return mid
            if cur < pos_ms:
                lo = mid + 1
            else:
                hi = mid - 1
        return max(0, hi)
