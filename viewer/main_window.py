from typing import List
from pathlib import Path
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from .video_player import VideoPlayerWidget
from .calendar_widget import CalendarWidget
from .window_data_timeline import WindowDataTimeline
from .filesystem_reader import FileSystemReader


class MainWindow(QMainWindow):
    def __init__(self, base_path: Path | None = None):
        super().__init__()
        self._base_path = base_path or Path(".")
        self._fs = FileSystemReader(self._base_path)
        self._video = VideoPlayerWidget()
        self._calendar = CalendarWidget(self._fs)
        self._window_list = WindowDataTimeline()

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._video)
        bottom = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom_layout.addWidget(self._calendar)
        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._video.get_controls_widget())
        right_layout.addWidget(self._window_list)
        right_layout.setStretch(0, 0)
        right_layout.setStretch(1, 1)
        right.setLayout(right_layout)
        bottom_layout.addWidget(right)
        bottom.setLayout(bottom_layout)
        layout.addWidget(bottom)
        layout.setStretch(0, 8)
        layout.setStretch(1, 2)
        bottom_layout.setStretch(0, 3)
        bottom_layout.setStretch(1, 7)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def on_date_selected(self, date: QDate):
        pass

    def display_video(self, video_path: Path):
        pass

    def display_error(self, message: str):
        pass

    def update_window_data(self, window_data: List):
        pass
