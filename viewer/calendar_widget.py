from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QTextCharFormat
from PyQt6.QtWidgets import QCalendarWidget


class CalendarWidget(QCalendarWidget):
    date_selected = pyqtSignal(QDate)
    error_occurred = pyqtSignal(str)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()

    def __init__(self, file_system_reader):
        super().__init__()
        self._fs = file_system_reader
        self._available_qdates: set[QDate] = set()
        self._video_qdates: set[QDate] = set()

        self.setGridVisible(True)
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)

        self.selectionChanged.connect(self._on_selection_changed)
        self.currentPageChanged.connect(self._on_page_changed)

        self.update_available_dates()

    def update_available_dates(self):
        self.loading_started.emit()
        prev_formatted = getattr(self, "_formatted_qdates", set())
        for d in prev_formatted:
            self.setDateTextFormat(d, QTextCharFormat())

        self._available_qdates = set()
        self._video_qdates = set()

        dates = self._fs.get_available_dates()
        err = getattr(self._fs, "last_error_msg", None)
        if err:
            self.error_occurred.emit(err)
        for d in dates:
            qd = QDate(d.year, d.month, d.day)
            self._available_qdates.add(qd)
            if self._fs.video_exists(d):
                self._video_qdates.add(qd)

        fmt_available = QTextCharFormat()
        fmt_available.setForeground(QColor(20, 120, 200))

        fmt_video = QTextCharFormat()
        fmt_video.setForeground(QColor(0, 140, 80))
        fmt_video.setFontWeight(600)

        for qd in self._available_qdates:
            self.setDateTextFormat(qd, fmt_available)
        for qd in self._video_qdates:
            self.setDateTextFormat(qd, fmt_video)

        self._formatted_qdates = set(self._available_qdates | self._video_qdates)
        self.loading_finished.emit()

    def paintCell(self, painter: QPainter, rect, date: QDate):
        super().paintCell(painter, rect, date)
        if date in self._available_qdates:
            color = (
                QColor(0, 140, 80)
                if date in self._video_qdates
                else QColor(20, 120, 200)
            )
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)
            r = min(rect.width(), rect.height())
            size = max(6, r // 8)
            x = rect.right() - size - 3
            y = rect.bottom() - size - 3
            painter.drawEllipse(x, y, size, size)

    def is_date_available(self, date: QDate) -> bool:
        return date in self._available_qdates

    def _on_selection_changed(self):
        d = self.selectedDate()
        if d in self._available_qdates:
            self.date_selected.emit(d)

    def _on_page_changed(self, year: int, month: int):
        self.update()
