from __future__ import annotations
from pathlib import Path
from datetime import datetime
import sys
import argparse
import logging

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtWidgets import QStyle

from viewer.filesystem_reader import FileSystemReader
from viewer.calendar_widget import CalendarWidget
from viewer.video_player import VideoPlayerWidget
from viewer.window_data_parser import WindowDataParser, WindowDataEntry
from viewer.window_data_timeline import WindowDataTimeline


class MainWindow(QMainWindow):
    def __init__(self, base_dir: Path | None = None):
        super().__init__()
        self._base_dir = base_dir or (Path.home() / "Documents" / "Screenshots")
        self._fs = FileSystemReader(self._base_dir)
        self._parser = WindowDataParser()

        self._calendar: CalendarWidget | None = None
        self._video_player: VideoPlayerWidget | None = None
        self._timeline: WindowDataTimeline | None = None
        self._current_date: QDate | None = None
        self._progress: QProgressBar | None = None

        self.setWindowTitle("Daily Progress Viewer")
        try:
            self.setWindowIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
        except Exception:
            pass
        self.setMinimumSize(1000, 650)
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        central.setLayout(root)
        self.setCentralWidget(central)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.hide()
        self.statusBar().addPermanentWidget(self._progress)

        self._video_player = VideoPlayerWidget()
        root.addWidget(self._video_player)

        bottom = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom.setLayout(bottom_layout)
        root.addWidget(bottom)

        self._calendar = CalendarWidget(self._fs)
        bottom_layout.addWidget(self._calendar)

        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right.setLayout(right_layout)
        bottom_layout.addWidget(right)

        right_layout.addWidget(self._video_player.get_controls_widget())

        self._timeline = WindowDataTimeline()
        right_layout.addWidget(self._timeline)

        right_layout.setStretch(0, 0)
        right_layout.setStretch(1, 1)

        root.setStretch(0, 8)
        root.setStretch(1, 2)
        bottom_layout.setStretch(0, 3)
        bottom_layout.setStretch(1, 7)

        self._calendar.date_selected.connect(self.on_date_selected)
        self._calendar.error_occurred.connect(self.on_component_error)
        self._video_player.error_occurred.connect(self.on_component_error)
        self._calendar.loading_started.connect(lambda: self._progress.show())
        self._calendar.loading_finished.connect(lambda: self._progress.hide())
        self._video_player.loading_changed.connect(
            lambda b: self._progress.setVisible(b)
        )

    def on_date_selected(self, date: QDate):
        self._current_date = date
        py_date = datetime(year=date.year(), month=date.month(), day=date.day()).date()

        self.statusBar().showMessage("Loading video…", 2000)
        video_path = self._fs.get_video_path(py_date)
        if video_path is None:
            try:
                logging.warning("No timelapse video available for date %s", py_date)
            except Exception:
                pass
            self.display_error("No timelapse video available for this date")
            if self._video_player:
                self._video_player.pause()
            if self._timeline:
                self._timeline.clear()
            return

        if self._video_player:
            self._video_player.load_video(video_path)

        entries: list[WindowDataEntry] = []
        wd_path = self._fs.get_window_data_path(py_date)
        if wd_path is not None:
            self.statusBar().showMessage("Loading window data…", 2000)
            if self._progress:
                self._progress.show()
            entries = self._parser.parse_file(wd_path)
            self.update_window_data(entries)
            if self._progress:
                self._progress.hide()
        else:
            if self._timeline:
                self._timeline.clear()

        video_start_dt: datetime | None = None
        if entries:
            video_start_dt = entries[0].timestamp
        else:
            video_start_dt = datetime(
                year=date.year(), month=date.month(), day=date.day()
            )

        if self._timeline and self._video_player and video_start_dt:
            self._timeline.bind_to_player(self._video_player, video_start_dt)

        if self._video_player and hasattr(self._video_player, "_player"):
            self._video_player._player.durationChanged.connect(
                lambda dur: self._timeline
                and self._timeline.set_video_timing(video_start_dt, int(dur))
            )

    def display_video(self, video_path: Path):
        if self._video_player:
            self._video_player.load_video(video_path)

    def display_error(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def on_component_error(self, message: str):
        try:
            logging.error(message)
        except Exception:
            pass
        self.display_error(message)

    def update_window_data(self, window_data: list[WindowDataEntry]):
        if self._timeline:
            self._timeline.load_window_data(window_data)

    def resizeEvent(self, event):
        super().resizeEvent(event)


def main():
    parser = argparse.ArgumentParser(description="Daily Progress Viewer")
    parser.add_argument(
        "--base-dir",
        "-b",
        help="Base screenshots directory",
        default=str(Path.home() / "Documents" / "Screenshots"),
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Daily Progress Viewer")
    try:
        app.setWindowIcon(
            QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        )
    except Exception:
        pass

    log_dir = Path.home() / ".logs" / "daily_progress_viewer"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"viewer_{datetime.now().strftime('%Y%m%d')}.log"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh = logging.FileHandler(str(log_file))
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    base_path = Path(args.base_dir)
    if not base_path.exists() or not base_path.is_dir():
        logging.error("Screenshots directory not found: %s", base_path)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("Screenshots directory not found")
        msg.setInformativeText(str(base_path))
        msg.exec()
        sys.exit(2)

    w = MainWindow(base_dir=base_path)
    w.show()
    rc = app.exec()
    sys.exit(rc)


if __name__ == "__main__":
    main()
