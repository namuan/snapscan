# Design Document: Daily Progress Viewer

## Overview

The Daily Progress Viewer is a standalone PyQt6 desktop application that provides users with an intuitive interface to review their daily computer activity through timelapse videos. The application operates independently from the SnapSpan menu bar screenshot capture tool and directly accesses the organized screenshot data stored in the file system.

The viewer features a calendar-based navigation system that allows users to select any day with available data and watch a timelapse video of their activity. The interface also displays synchronized window and application data, providing context about what the user was working on throughout the day.

### Key Design Goals

1. **Separation of Concerns**: The viewer operates as a completely independent application from the screenshot capture system
2. **Direct File System Access**: No database or intermediate storage layer - reads directly from the organized directory structure
3. **Video-First Experience**: Prioritizes timelapse video playback as the primary way to review daily activity
4. **Responsive UI**: Fast loading and smooth interactions using PyQt6's native capabilities
5. **Graceful Degradation**: Handles missing or corrupted data without crashing

## Architecture

The application follows a Model-View-Controller (MVC) architectural pattern adapted for PyQt6:

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    Main Window (View)                    │
│  ┌──────────────┐  ┌─────────────────────────────────┐ │
│  │   Calendar   │  │      Video Player Area          │ │
│  │   Widget     │  │  ┌───────────────────────────┐  │ │
│  │              │  │  │   QMediaPlayer/QVideoWidget│  │ │
│  │              │  │  └───────────────────────────┘  │ │
│  │              │  │  ┌───────────────────────────┐  │ │
│  │              │  │  │   Playback Controls       │  │ │
│  │              │  │  └───────────────────────────┘  │ │
│  └──────────────┘  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐│
│  │         Window Data Timeline Panel                  ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Application Controller                      │
│  • Handles user interactions                            │
│  • Coordinates between UI and data layer                │
│  • Manages application state                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Access Layer                       │
│  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │ FileSystemReader│  │  WindowDataParser            │ │
│  │ • Scans dirs    │  │  • Parses JSONL              │ │
│  │ • Finds videos  │  │  • Matches timestamps        │ │
│  │ • Validates     │  │  • Handles errors            │ │
│  └─────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    File System                           │
│         ~/Documents/Screenshots/YYYY/MM/DD/             │
│         • timelapse-YYYYMMDD.mp4                        │
│         • window_data.jsonl                             │
│         • YYYYMMDD_HHMMSS.png (screenshots)             │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Main Window (View Layer)**
- Renders the UI using PyQt6 widgets
- Displays calendar, video player, and window data
- Forwards user interactions to the controller
- Updates display based on controller commands

**Application Controller**
- Processes user input (date selection, playback controls)
- Coordinates data loading from the file system
- Manages application state (current date, playback position)
- Handles error conditions and user feedback

**Data Access Layer**
- `FileSystemReader`: Scans directory structure, validates paths, finds available dates
- `WindowDataParser`: Reads and parses window_data.jsonl files, matches timestamps to video position

## Components and Interfaces

### 1. Main Window (`MainWindow`)

The primary UI container that hosts all visual components.

**Responsibilities:**
- Initialize and layout all UI widgets
- Handle window resize events
- Coordinate between calendar and video player components

**Key Methods:**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        """Initialize the main window and all child widgets"""

    def setup_ui(self):
        """Create and layout all UI components"""

    def on_date_selected(self, date: QDate):
        """Handle date selection from calendar"""

    def display_video(self, video_path: Path):
        """Load and display the timelapse video"""

    def display_error(self, message: str):
        """Show error message to user"""

    def update_window_data(self, window_data: List[WindowDataEntry]):
        """Update the window data timeline display"""
```

### 2. Calendar Widget (`CalendarWidget`)

Custom calendar widget that shows available dates and handles date selection.

**Responsibilities:**
- Display monthly calendar view
- Highlight dates with available data
- Disable dates without data
- Emit signals when user selects a date

**Key Methods:**
```python
class CalendarWidget(QCalendarWidget):
    date_selected = pyqtSignal(QDate)

    def __init__(self, file_system_reader: FileSystemReader):
        """Initialize calendar with file system reader"""

    def update_available_dates(self):
        """Scan file system and update date availability"""

    def paint_cell(self, painter: QPainter, rect: QRect, date: QDate):
        """Custom painting for dates with/without data"""

    def is_date_available(self, date: QDate) -> bool:
        """Check if date has available data"""
```

### 3. Video Player Component (`VideoPlayerWidget`)

Embedded video player with playback controls.

**Responsibilities:**
- Display timelapse video
- Provide playback controls (play, pause, seek, volume)
- Emit signals for playback position changes
- Handle video loading errors

**Key Methods:**
```python
class VideoPlayerWidget(QWidget):
    position_changed = pyqtSignal(int)  # milliseconds
    playback_state_changed = pyqtSignal(QMediaPlayer.PlaybackState)

    def __init__(self):
        """Initialize video player and controls"""

    def load_video(self, video_path: Path):
        """Load video file into player"""

    def play(self):
        """Start video playback"""

    def pause(self):
        """Pause video playback"""

    def seek(self, position_ms: int):
        """Seek to specific position in video"""

    def set_volume(self, volume: int):
        """Set playback volume (0-100)"""

    def get_duration(self) -> int:
        """Get total video duration in milliseconds"""

    def get_position(self) -> int:
        """Get current playback position in milliseconds"""
```

### 4. Window Data Timeline (`WindowDataTimeline`)

Panel that displays application and window information synchronized with video playback.

**Responsibilities:**
- Display window data entries in a timeline or list
- Highlight current entry based on video position
- Show active application and window titles
- Handle missing or malformed data gracefully

**Key Methods:**
```python
class WindowDataTimeline(QWidget):
    def __init__(self):
        """Initialize timeline widget"""

    def load_window_data(self, entries: List[WindowDataEntry]):
        """Load and display window data entries"""

    def update_current_position(self, video_position_ms: int):
        """Highlight entry corresponding to video position"""

    def clear(self):
        """Clear all displayed data"""
```

### 5. File System Reader (`FileSystemReader`)

Handles all file system operations for reading screenshot data.

**Responsibilities:**
- Scan directory structure to find available dates
- Validate directory and file existence
- Return paths to timelapse videos
- Handle file system errors

**Key Methods:**
```python
class FileSystemReader:
    def __init__(self, base_path: Path):
        """Initialize with base screenshots directory"""

    def get_available_dates(self) -> List[date]:
        """Scan file system and return list of dates with data"""

    def get_video_path(self, date: date) -> Optional[Path]:
        """Get path to timelapse video for specific date"""

    def video_exists(self, date: date) -> bool:
        """Check if timelapse video exists for date"""

    def get_window_data_path(self, date: date) -> Optional[Path]:
        """Get path to window data file for specific date"""

    def validate_base_directory(self) -> bool:
        """Check if base screenshots directory exists"""
```

### 6. Window Data Parser (`WindowDataParser`)

Parses and processes window_data.jsonl files.

**Responsibilities:**
- Read JSONL file line by line
- Parse JSON entries into structured data
- Handle malformed JSON gracefully
- Match timestamps to video positions

**Key Methods:**
```python
class WindowDataParser:
    def parse_file(self, file_path: Path) -> List[WindowDataEntry]:
        """Parse window data file and return list of entries"""

    def parse_line(self, line: str) -> Optional[WindowDataEntry]:
        """Parse single JSONL line into WindowDataEntry"""

    def match_timestamp_to_video_position(
        self,
        timestamp: datetime,
        video_start: datetime,
        video_duration_ms: int
    ) -> int:
        """Calculate video position (ms) for given timestamp"""
```

## Data Models

### WindowDataEntry

Represents a single entry from the window_data.jsonl file.

```python
@dataclass
class WindowDataEntry:
    timestamp: datetime
    windows: List[WindowInfo]

    @property
    def active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window"""
        return next((w for w in self.windows if w.is_active), None)
```

### WindowInfo

Represents information about a single window.

```python
@dataclass
class WindowInfo:
    app_name: str
    window_name: str
    is_active: bool
```

### DateInfo

Represents metadata about a date with available data.

```python
@dataclass
class DateInfo:
    date: date
    has_video: bool
    has_window_data: bool
    video_path: Optional[Path]
    window_data_path: Optional[Path]
```


## Error Handling

The application implements a multi-layered error handling strategy:

### File System Errors

**Missing Base Directory**
- Check: On application startup, validate that `~/Documents/Screenshots` exists
- Action: Display error dialog with instructions to run SnapSpan first or check installation
- Recovery: Allow user to specify alternative directory or exit application

**Missing Date Directory**
- Check: When scanning for available dates, skip directories that don't match YYYY/MM/DD pattern
- Action: Simply don't enable those dates in the calendar
- Recovery: Automatic - only valid dates are shown

**Permission Errors**
- Check: Catch permission exceptions when accessing files or directories
- Action: Display error message indicating permission issue with specific path
- Recovery: Log error and continue with other operations where possible

### Video File Errors

**Missing Video File**
- Check: Before attempting to load video, verify file exists
- Action: Display message "No timelapse video available for this date"
- Recovery: Allow user to select different date

**Corrupted Video File**
- Check: Catch QMediaPlayer errors during video loading
- Action: Display error message with details about the corrupted file
- Recovery: Log error, allow user to select different date

**Unsupported Video Format**
- Check: QMediaPlayer will emit error if format is unsupported
- Action: Display error message indicating format issue
- Recovery: Log error, suggest regenerating timelapse

### Window Data Errors

**Missing Window Data File**
- Check: Before parsing, verify file exists
- Action: Display video without window data timeline
- Recovery: Automatic - video playback continues normally

**Malformed JSON**
- Check: Wrap JSON parsing in try-except blocks
- Action: Skip malformed lines, log warning
- Recovery: Continue parsing remaining lines, display partial data

**Timestamp Mismatch**
- Check: Validate that window data timestamps fall within video duration
- Action: Display window data but may not sync perfectly
- Recovery: Show all data, highlight closest match

### UI Errors

**Widget Initialization Failure**
- Check: Validate widget creation in try-except blocks
- Action: Log error and display minimal fallback UI
- Recovery: Attempt to continue with reduced functionality

**Resource Loading Failure**
- Check: Validate that required resources (icons, styles) load successfully
- Action: Use default system styling if custom resources fail
- Recovery: Automatic fallback to defaults

### Error Logging

All errors are logged to a file with the following information:
- Timestamp
- Error level (ERROR, WARNING, INFO)
- Component that generated the error
- Error message and stack trace
- Relevant context (file path, user action, etc.)

Log file location: `~/.logs/daily_progress_viewer/viewer_YYYYMMDD.log`

## Testing Strategy

For the MVP, we will focus on manual testing and basic error handling. Automated testing will be added in future iterations.

### Manual Testing Checklist

**Application Launch**
- Verify application launches successfully
- Verify it runs independently from SnapSpan menu bar app
- Verify window displays correctly

**Calendar Functionality**
- Verify calendar shows current month on launch
- Verify navigation between months works
- Verify dates with data are enabled
- Verify dates without data are disabled
- Verify visual styling for dates with videos

**Video Playback**
- Verify video loads when date is selected
- Verify play/pause controls work
- Verify seek slider works
- Verify volume control works
- Verify video metadata (duration, position) displays

**Window Data Display**
- Verify window data loads and displays
- Verify synchronization with video playback
- Verify graceful handling when window data is missing

**Error Handling**
- Verify error message when base directory doesn't exist
- Verify error message when video file is missing
- Verify graceful handling of corrupted files
