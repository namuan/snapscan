# Requirements Document

## Introduction

This document specifies the requirements for a Daily Progress Viewer UI for the SnapSpan application. The Daily Progress Viewer is a standalone PyQt6-based graphical user interface that enables users to visualize their daily computer activity by browsing through captured screenshots organized by date. The viewer will operate independently from the existing menu bar application and directly access screenshot data from the file system.

## Glossary

- **Daily Progress Viewer**: The standalone PyQt6 application that displays screenshots and activity data
- **Screenshot Directory**: The base directory at `~/Documents/Screenshots` containing organized screenshot data
- **Calendar Widget**: The interactive date selection component in the UI
- **Screenshot Timeline**: The chronological display of screenshots for a selected day
- **Window Data**: JSON-formatted log entries containing application and window information
- **Timelapse Video**: MP4 video file generated from daily screenshots
- **SnapSpan**: The existing menu bar application that captures screenshots

## Requirements

### Requirement 1

**User Story:** As a user, I want to launch a standalone viewer application, so that I can review my daily progress without interfering with the screenshot capture process.

#### Acceptance Criteria

1. WHEN the user executes the viewer application THEN the Daily Progress Viewer SHALL launch as a separate process from the SnapSpan menu bar application
2. WHEN the Daily Progress Viewer is running THEN the system SHALL continue screenshot capture operations without interruption
3. WHEN the user closes the Daily Progress Viewer THEN the system SHALL terminate only the viewer process while preserving the SnapSpan menu bar application
4. THE Daily Progress Viewer SHALL initialize within 3 seconds on standard hardware

### Requirement 2

**User Story:** As a user, I want to see a calendar interface, so that I can easily select any day to review my activity.

#### Acceptance Criteria

1. WHEN the Daily Progress Viewer launches THEN the system SHALL display a calendar widget showing the current month
2. WHEN the user navigates to different months THEN the system SHALL update the calendar display to show the selected month
3. WHEN the user clicks on a date with available data THEN the system SHALL load and display the timelapse video for that specific date
4. WHEN a date directory exists at `~/Documents/Screenshots/YYYY/MM/DD/` THEN the system SHALL enable that date in the calendar for selection
5. WHEN a date directory does not exist THEN the system SHALL disable that date in the calendar and prevent selection
6. WHEN a date contains a timelapse video THEN the system SHALL visually indicate that date in the calendar with distinct styling

### Requirement 3

**User Story:** As a user, I want to watch the timelapse video for a selected day, so that I can quickly review the entire day's activity.

#### Acceptance Criteria

1. WHEN the user selects a date THEN the system SHALL check for the timelapse video file at `~/Documents/Screenshots/YYYY/MM/DD/timelapse-YYYYMMDD.mp4`
2. WHEN a timelapse video exists for the selected date THEN the system SHALL display the video in an embedded video player within the UI
3. WHEN the user plays the video THEN the system SHALL provide standard video controls including play, pause, seek, and volume
4. WHEN no timelapse video exists for the selected date THEN the system SHALL display a message indicating the video is not available
5. WHEN the video player loads THEN the system SHALL display the video duration and current playback position

### Requirement 4

**User Story:** As a user, I want to control video playback, so that I can review specific moments in my daily progress.

#### Acceptance Criteria

1. WHEN the user clicks the play button THEN the system SHALL begin playing the timelapse video
2. WHEN the user clicks the pause button THEN the system SHALL pause video playback at the current position
3. WHEN the user drags the seek slider THEN the system SHALL update the video position to the selected timestamp
4. WHEN the user adjusts the volume control THEN the system SHALL change the video playback volume accordingly
5. WHEN the video reaches the end THEN the system SHALL stop playback and reset to the beginning

### Requirement 5

**User Story:** As a user, I want to see window and application data alongside the video, so that I can understand what I was working on throughout the day.

#### Acceptance Criteria

1. WHEN playing the timelapse video THEN the system SHALL load window data from `window_data.jsonl` for the selected date
2. WHEN window data exists THEN the system SHALL display a timeline or list showing application activity throughout the day
3. WHEN the video playback position changes THEN the system SHALL highlight the corresponding window data entry for that timestamp
4. WHEN no window data exists for the selected date THEN the system SHALL display the video without window information
5. WHEN parsing window data THEN the system SHALL handle malformed JSON entries gracefully without crashing

### Requirement 6

**User Story:** As a user, I want the UI to be responsive and intuitive, so that I can efficiently navigate and review my daily progress.

#### Acceptance Criteria

1. THE Daily Progress Viewer SHALL use PyQt6 framework for all UI components
2. WHEN the user resizes the window THEN the system SHALL adjust the layout to maintain usability
3. WHEN displaying video THEN the system SHALL scale content to fit the viewing area while maintaining aspect ratio
4. WHEN the UI performs long-running operations THEN the system SHALL display a loading indicator to provide feedback
5. WHEN the user interacts with UI controls THEN the system SHALL respond within 100 milliseconds

### Requirement 7

**User Story:** As a user, I want the viewer to handle missing or corrupted data gracefully, so that I can continue using the application even when some data is unavailable.

#### Acceptance Criteria

1. WHEN the Screenshot Directory does not exist THEN the system SHALL display an error message and provide guidance to the user
2. WHEN a timelapse video file is corrupted or unreadable THEN the system SHALL display an error message with details
3. WHEN the window data file is corrupted THEN the system SHALL display the video without window information
4. WHEN file system permissions prevent reading THEN the system SHALL display an appropriate error message
5. WHEN encountering errors THEN the system SHALL log error details for debugging purposes
