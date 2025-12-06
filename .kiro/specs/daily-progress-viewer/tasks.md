# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create `viewer.py` as the main entry point for the Daily Progress Viewer
  - Add PyQt6 and PyQt6-Multimedia to requirements.txt
  - Create directory structure for viewer components
  - _Requirements: 1.1, 6.1_

- [x] 2. Implement data access layer
- [x] 2.1 Create FileSystemReader class
  - Implement base directory validation
  - Implement method to scan and return available dates
  - Implement method to get video path for a specific date
  - Implement method to get window data path for a specific date
  - _Requirements: 2.4, 2.5, 3.1, 7.1_

- [x] 2.2 Create WindowDataParser class
  - Implement JSONL file parsing
  - Implement graceful handling of malformed JSON entries
  - Implement data model classes (WindowDataEntry, WindowInfo)
  - _Requirements: 5.1, 5.5, 7.3_

- [x] 3. Implement calendar widget
- [x] 3.1 Create CalendarWidget class
  - Extend QCalendarWidget with custom functionality
  - Implement date availability checking using FileSystemReader
  - Implement custom cell painting for visual indication of dates with videos
  - Implement date selection signal emission
  - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6_

- [x] 3.2 Implement date enabling/disabling logic
  - Scan file system on calendar initialization
  - Enable dates with existing directories
  - Disable dates without directories
  - Update calendar display when month changes
  - _Requirements: 2.4, 2.5_

- [x] 4. Implement video player component
- [x] 4.1 Create VideoPlayerWidget class
  - Set up QMediaPlayer and QVideoWidget
  - Implement video loading from file path
  - Implement basic play/pause functionality
  - Handle video loading errors gracefully
  - _Requirements: 3.2, 3.4, 4.1, 4.2, 7.2_

- [x] 4.2 Add playback controls UI
  - Create play/pause button
  - Create seek slider for video position
  - Create volume slider
  - Display video duration and current position
  - _Requirements: 3.3, 3.5, 4.1, 4.2, 4.3, 4.4_

- [x] 4.3 Implement playback control logic
  - Connect play/pause button to media player
  - Implement seek functionality with slider
  - Implement volume control
  - Handle end-of-video behavior
  - Emit position change signals for synchronization
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Implement window data timeline
- [x] 5.1 Create WindowDataTimeline widget
  - Design layout for displaying window data entries
  - Implement method to load and display window data
  - Implement highlighting of current entry based on video position
  - Handle missing window data gracefully
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5.2 Implement video-window data synchronization
  - Connect video player position changes to timeline updates
  - Calculate which window data entry corresponds to current video position
  - Update timeline highlighting as video plays
  - _Requirements: 5.3_

- [x] 6. Implement main window
- [x] 6.1 Create MainWindow class
  - Set up main window layout with calendar on left, video player on right
  - Add window data timeline panel below video player
  - Implement window resize handling
  - Set minimum window size
  - _Requirements: 1.1, 6.2_

- [x] 6.2 Wire up component interactions
  - Connect calendar date selection to video loading
  - Connect video player to window data timeline
  - Implement error message display
  - Add loading indicators for long operations
  - _Requirements: 2.3, 6.4_

- [x] 7. Implement error handling and logging
- [x] 7.1 Set up logging system
  - Create log directory at ~/.logs/daily_progress_viewer/
  - Configure logging with timestamps and levels
  - Implement error logging for all error conditions
  - _Requirements: 7.5_

- [x] 7.2 Add error dialogs and messages
  - Implement error dialog for missing base directory
  - Implement error message for missing video
  - Implement error message for corrupted files
  - Implement error message for permission issues
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 8. Implement responsive UI features
 - [x] 8.1 Add video scaling and aspect ratio preservation
  - Configure video widget to scale while maintaining aspect ratio
  - Handle different video sizes and window sizes
  - _Requirements: 6.3_

- [x] 8.2 Add loading indicators
  - Create loading spinner or progress indicator
  - Show indicator when scanning directories
  - Show indicator when loading video
  - Hide indicator when operations complete
  - _Requirements: 6.4_

- [x] 9. Create application entry point
- [x] 9.1 Implement main function in viewer.py
  - Initialize QApplication
  - Create and show MainWindow
  - Handle application lifecycle
  - Ensure clean shutdown
  - _Requirements: 1.1, 1.3_

- [x] 9.2 Add command-line interface
  - Add optional argument for custom screenshots directory
  - Add help text and usage information
  - _Requirements: 1.1_

- [x] 10. Final integration and polish
- [x] 10.1 Test complete workflow
  - Verify application launches independently
  - Test date selection and video playback
  - Test window data synchronization
  - Test error handling scenarios
  - _Requirements: All_

- [x] 10.2 Add UI polish
  - Set application icon
  - Set window title
  - Improve styling and spacing
  - Add tooltips to controls
  - _Requirements: 6.2_
