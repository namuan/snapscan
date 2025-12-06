# Daily Progress Viewer

## Overview

The Daily Progress Viewer is a PyQt6 desktop UI that lets you browse timelapse videos of your screen activity by day and correlate playback with a timestamped window-activity timeline.

- Entry point: `viewer.py` (MainWindow) at `viewer.py:27`.
- Core UI modules in `viewer/`: calendar, video player, filesystem access, window data parsing, and timeline.
- Expected data layout under a base directory: `YYYY/MM/DD/` containing a daily timelapse `timelapse-YYYYMMDD.mp4` and optional `window_data.jsonl`.

## Features

- Calendar-driven browsing with availability and video indicators (`viewer/calendar_widget.py:6`).
- Timelapse video playback with controls and status (`viewer/video_player.py:16`).
- Timeline table showing active app/window across the day (`viewer/window_data_timeline.py:9`).
- Automatic mapping of window timestamps to video positions (`viewer/window_data_parser.py:74`).
- Robust filesystem scanning and error reporting (`viewer/filesystem_reader.py:7`).
- Progress feedback during data and media loading (`viewer.py:58`).

## Usage

- Prepare the base directory with this structure:
  - `/<base-dir>/<YYYY>/<MM>/<DD>/timelapse-YYYYMMDD.mp4`
  - `/<base-dir>/<YYYY>/<MM>/<DD>/window_data.jsonl` (optional)
- Run the viewer:
  ```bash
  python viewer.py --base-dir ~/Documents/Screenshots
  ```
- Interact with the UI:
  - Select a date in the calendar; available days are tinted, days with video are bold green (`viewer/calendar_widget.py:45`).
  - If a video exists for the selected date, playback loads with controls; otherwise, an error dialog appears (`viewer.py:110`–`viewer.py:119`, `viewer.py:161`–`viewer.py:169`).
  - If `window_data.jsonl` exists, the timeline table populates and tracks the current playback position (`viewer.py:126`–`viewer.py:136`, `viewer/window_data_timeline.py:71`–`viewer/window_data_timeline.py:74`).

## API Methods

### `MainWindow` (app shell)
- Location: `viewer.py:27`
- Purpose: Composes calendar, player, and timeline; wires signals; orchestrates loading.
- Methods:
  - `setup_ui()` (`viewer.py:50`): Build layouts and connect signals.
  - `on_date_selected(date: QDate)` (`viewer.py:105`): Load video and window data for selected date; bind timeline to player.
  - `display_video(video_path: Path)` (`viewer.py:157`): Delegate to player.
  - `display_error(message: str)` (`viewer.py:161`): Show critical dialog.
  - `on_component_error(message: str)` (`viewer.py:164`): Log and display errors from child components.
  - `update_window_data(window_data: list[WindowDataEntry])` (`viewer.py:171`): Load into timeline.

### `CalendarWidget`
- Location: `viewer/calendar_widget.py:6`
- Purpose: Shows monthly calendar and indicates data availability.
- Signals:
  - `date_selected(QDate)` (`viewer/calendar_widget.py:7`)
  - `error_occurred(str)` (`viewer/calendar_widget.py:8`)
  - `loading_started()` (`viewer/calendar_widget.py:9`)
  - `loading_finished()` (`viewer/calendar_widget.py:10`)
- Methods:
  - `update_available_dates()` (`viewer/calendar_widget.py:26`): Query filesystem and mark calendar cells.
  - `is_date_available(date: QDate) -> bool` (`viewer/calendar_widget.py:77`)

### `VideoPlayerWidget`
- Location: `viewer/video_player.py:16`
- Purpose: Plays MP4 with controls and status.
- Signals:
  - `position_changed(int)` (`viewer/video_player.py:17`)
  - `playback_state_changed(QMediaPlayer.PlaybackState)` (`viewer/video_player.py:18`)
  - `error_occurred(str)` (`viewer/video_player.py:19`)
  - `loading_changed(bool)` (`viewer/video_player.py:20`)
- Methods:
  - `load_video(video_path: Path)` (`viewer/video_player.py:85`)
  - `play()` / `pause()` (`viewer/video_player.py:95`, `viewer/video_player.py:98`)
  - `seek(position_ms: int)` (`viewer/video_player.py:101`)
  - `set_volume(volume: int)` (`viewer/video_player.py:104`)
  - `get_duration() -> int` (`viewer/video_player.py:108`)
  - `get_position() -> int` (`viewer/video_player.py:111`)
  - `get_controls_widget() -> QWidget` (`viewer/video_player.py:180`)

### `FileSystemReader`
- Location: `viewer/filesystem_reader.py:7`
- Purpose: Discover available dates and resolve data paths.
- Properties:
  - `base_path: Path` (`viewer/filesystem_reader.py:8`)
  - `last_error_msg: Optional[str>` (`viewer/filesystem_reader.py:10`)
- Methods:
  - `validate_base_directory() -> bool` (`viewer/filesystem_reader.py:76`)
  - `get_available_dates() -> list[datetime.date]` (`viewer/filesystem_reader.py:12`)
  - `get_video_path(d: datetime.date) -> Optional[Path]` (`viewer/filesystem_reader.py:48`)
  - `video_exists(d: datetime.date) -> bool` (`viewer/filesystem_reader.py:61`)
  - `get_window_data_path(d: datetime.date) -> Optional[Path]` (`viewer/filesystem_reader.py:64`)

### `WindowDataParser` and models
- Location: `viewer/window_data_parser.py`
- Models:
  - `WindowInfo` (`viewer/window_data_parser.py:10`): `{ app_name, window_name, is_active }`.
  - `WindowDataEntry` (`viewer/window_data_parser.py:17`): `{ timestamp: datetime, windows: list[WindowInfo] }` with `active_window` (`viewer/window_data_parser.py:21`).
- Methods:
  - `parse_file(file_path: Path) -> list[WindowDataEntry]` (`viewer/window_data_parser.py:27`)
  - `parse_line(line: str) -> WindowDataEntry | None` (`viewer/window_data_parser.py:45`)
  - `match_timestamp_to_video_position(timestamp, video_start, video_duration_ms) -> int` (`viewer/window_data_parser.py:74`)

### `WindowDataTimeline`
- Location: `viewer/window_data_timeline.py:9`
- Purpose: Displays window activity and tracks current playback time.
- Methods:
  - `load_window_data(entries: list[WindowDataEntry])` (`viewer/window_data_timeline.py:27`)
  - `update_current_position(video_position_ms: int)` (`viewer/window_data_timeline.py:45`)
  - `clear()` (`viewer/window_data_timeline.py:58`)
  - `set_video_timing(video_start: datetime, video_duration_ms: int)` (`viewer/window_data_timeline.py:65`)
  - `bind_to_player(player: VideoPlayerWidget, video_start: datetime)` (`viewer/window_data_timeline.py:71`)

## Parameters

- CLI `--base-dir` (`viewer.py:181`): Path to the screenshots/timelapse root.
  - Default: `~/Documents/Screenshots` (`viewer.py:30`, `viewer.py:184`–`viewer.py:186`).
- File naming conventions:
  - Video: `timelapse-YYYYMMDD.mp4` (`viewer/filesystem_reader.py:53`).
  - Window data: `window_data.jsonl` (`viewer/filesystem_reader.py:69`).

## Examples

### Launch the viewer with a custom base directory
```bash
python viewer.py --base-dir /path/to/Screenshots
```

### Embed the components in another PyQt application
```python
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from viewer.filesystem_reader import FileSystemReader
from viewer.calendar_widget import CalendarWidget
from viewer.video_player import VideoPlayerWidget
from viewer.window_data_timeline import WindowDataTimeline

app = QApplication([])
fs = FileSystemReader(Path('/path/to/Screenshots'))
cal = CalendarWidget(fs)
player = VideoPlayerWidget()
timeline = WindowDataTimeline()

# Bind timeline to player once you know the video's start timestamp
from datetime import datetime
video_start = datetime(2025, 12, 6)  # or first entry timestamp
timeline.bind_to_player(player, video_start)

# Connect calendar selection to loading logic
from PyQt6.QtCore import QDate

def on_date_selected(qd: QDate):
    py_date = datetime(qd.year(), qd.month(), qd.day()).date()
    video_path = fs.get_video_path(py_date)
    if video_path:
        player.load_video(video_path)
    wd_path = fs.get_window_data_path(py_date)
    if wd_path:
        from viewer.window_data_parser import WindowDataParser
        entries = WindowDataParser().parse_file(wd_path)
        timeline.load_window_data(entries)
        timeline.set_video_timing(video_start, player.get_duration())

cal.date_selected.connect(on_date_selected)

# Show your own window and add widgets as needed
```

### Parse window data directly
```python
from pathlib import Path
from viewer.window_data_parser import WindowDataParser

entries = WindowDataParser().parse_file(Path('/base/YYYY/MM/DD/window_data.jsonl'))
for e in entries:
    aw = e.active_window
    if aw:
        print(e.timestamp, aw.app_name, aw.window_name)
```

## Notes

- Dependencies: `PyQt6` and `PyQt6.QtMultimedia` for playback; see `requirements.txt` (`requirements.txt:7`).
- Error handling: Filesystem and media errors are surfaced via signals and dialogs (`viewer/filesystem_reader.py:40`–`viewer/filesystem_reader.py:46`, `viewer/video_player.py:149`–`viewer/video_player.py:178`, `viewer.py:161`–`viewer.py:169`).
- Progress feedback: Calendar and player emit loading signals to toggle a status bar progress bar (`viewer.py:58`–`viewer.py:63`, `viewer.py:99`–`viewer.py:103`).
- Platform: Tested with macOS paths and logging; video playback depends on platform codecs.
- Data alignment: Timeline aligns by first entry timestamp when available; otherwise the midnight of the selected date is used (`viewer.py:141`–`viewer.py:149`).
- Performance: Timeline uses binary search to keep selection in sync during playback (`viewer/window_data_timeline.py:84`–`viewer/window_data_timeline.py:101`).
