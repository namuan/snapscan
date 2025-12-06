from pathlib import Path
from PyQt6.QtCore import pyqtSignal, QUrl, Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QSizePolicy,
)


class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(int)
    playback_state_changed = pyqtSignal(QMediaPlayer.PlaybackState)
    error_occurred = pyqtSignal(str)
    loading_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._video = QVideoWidget()
        self._player.setVideoOutput(self._video)
        self._video.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._video.setMinimumSize(320, 240)

        self._play_btn = QPushButton("Play")
        self._play_btn.setToolTip("Play/Pause video")
        self._position_slider = QSlider(Qt.Orientation.Horizontal)
        self._position_slider.setRange(0, 0)
        self._position_slider.setToolTip("Seek video position")
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(50)
        self._volume_slider.setToolTip("Adjust playback volume")
        self._duration_label = QLabel("00:00")
        self._duration_label.setToolTip("Total duration")
        self._position_label = QLabel("00:00")
        self._position_label.setToolTip("Current playback position")
        self._status_label = QLabel()

        top = QVBoxLayout()
        top.setContentsMargins(8, 8, 8, 8)
        top.setSpacing(8)
        top.addWidget(self._video)
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(0, 0, 0, 0)
        ctrl.setSpacing(10)
        ctrl.addWidget(self._play_btn)
        ctrl.addWidget(self._position_label)
        ctrl.addWidget(self._position_slider)
        ctrl.addWidget(self._duration_label)
        ctrl.addWidget(QLabel("Vol"))
        ctrl.addWidget(self._volume_slider)
        top.addLayout(ctrl)
        top.addWidget(self._status_label)
        self.setLayout(top)

        self._play_btn.clicked.connect(self._toggle_play)
        self._position_slider.sliderMoved.connect(self._on_slider_moved)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        try:
            self._player.errorOccurred.connect(self._on_error)
        except AttributeError:
            pass

    def load_video(self, video_path: Path):
        if not video_path.exists() or not video_path.is_file():
            self._status_label.setText("Video not available")
            return
        self._status_label.setText("")
        self.loading_changed.emit(True)
        self._player.setSource(QUrl.fromLocalFile(str(video_path)))
        self._player.setPosition(0)
        self._position_slider.setValue(0)

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def seek(self, position_ms: int):
        self._player.setPosition(max(0, position_ms))

    def set_volume(self, volume: int):
        v = max(0, min(100, volume))
        self._audio.setVolume(v / 100.0)

    def get_duration(self) -> int:
        return int(self._player.duration())

    def get_position(self) -> int:
        return int(self._player.position())

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_slider_moved(self, val: int):
        self._player.setPosition(val)

    def _on_volume_changed(self, val: int):
        self._audio.setVolume(val / 100.0)

    def _on_position_changed(self, pos: int):
        self._position_slider.blockSignals(True)
        self._position_slider.setValue(pos)
        self._position_slider.blockSignals(False)
        self.position_changed.emit(pos)
        self._position_label.setText(self._fmt_ms(pos))

    def _on_duration_changed(self, dur: int):
        self._position_slider.setRange(0, dur)
        self._duration_label.setText(self._fmt_ms(dur))

    def _on_playback_state_changed(self, st: QMediaPlayer.PlaybackState):
        self.playback_state_changed.emit(st)
        self._play_btn.setText(
            "Pause" if st == QMediaPlayer.PlaybackState.PlayingState else "Play"
        )

    def _fmt_ms(self, ms: int) -> str:
        s = max(0, int(ms // 1000))
        m = s // 60
        r = s % 60
        return f"{m:02d}:{r:02d}"

    def _on_media_status_changed(self, st: QMediaPlayer.MediaStatus):
        if st == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.pause()
            self._player.setPosition(0)
            self._position_slider.setValue(0)
        if st == QMediaPlayer.MediaStatus.InvalidMedia:
            msg = "Error loading video"
            self._status_label.setText(msg)
            self.error_occurred.emit(msg)
            self.loading_changed.emit(False)
        elif st == QMediaPlayer.MediaStatus.LoadingMedia:
            self.loading_changed.emit(True)
        else:
            if st in (
                QMediaPlayer.MediaStatus.BufferedMedia,
                QMediaPlayer.MediaStatus.StalledMedia,
                QMediaPlayer.MediaStatus.LoadedMedia,
                QMediaPlayer.MediaStatus.NoMedia,
                QMediaPlayer.MediaStatus.BufferingMedia,
                QMediaPlayer.MediaStatus.BufferedMedia,
            ):
                self.loading_changed.emit(False)

    def _on_error(self, *args):
        msg = "Error loading video"
        if len(args) >= 2 and isinstance(args[1], str):
            msg = args[1]
        self._status_label.setText(msg)
        self.error_occurred.emit(msg)
        self.loading_changed.emit(False)
