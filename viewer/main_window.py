from typing import List
from pathlib import Path
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

    def setup_ui(self):
        pass

    def on_date_selected(self, date: QDate):
        pass

    def display_video(self, video_path: Path):
        pass

    def display_error(self, message: str):
        pass

    def update_window_data(self, window_data: List):
        pass
