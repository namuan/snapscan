# 📸 SnapSpan

One click, all screens, unified

## Features

- Capture screenshots from multiple monitors
- Scale up images to match the highest resolution
- Stitch images together
- Save screenshots with optimization and compression
- Detect changes between consecutive screenshots
- Schedule screenshot captures at regular intervals (every 60 seconds)
- Save timestamped list of all running applications
- Highlight currently active window

## Usage

1. Run the application using `python main.py`
2. Click on the menu bar icon to access scheduling options
3. Choose from "Start Scheduling" or "Stop Scheduling"
4. Interval for scheduled screenshot captures (default: 60 seconds)

## Timelapse Video

- Generate a timelapse MP4 from screenshots captured for a specific date.
- Requires `ffmpeg` installed and available on your PATH.

Commands:
- `python timelapse.py --date YYYY-MM-DD`
- `python timelapse.py --date YYYY-MM-DD --fps 24`
- `python timelapse.py --date YYYY-MM-DD --output /path/to/out.mp4`
- `python timelapse.py --date YYYY-MM-DD --delete` (deletes screenshots after success)

```shell
python timelapse.py --date 2025-10-21
```
```shell
python timelapse.py --date 2025-10-21 --fps 24
```
```shell
python timelapse.py --date 2025-10-21 --output /tmp/out.mp4
```
```shell
python timelapse.py --date 2025-10-21 --overwrite
```
```shell
python timelapse.py --date 2025-10-21 --delete
```

Output:
- Default output: `~/Documents/Screenshots/YYYY/MM/DD/timelapse-YYYYMMDD.mp4`

Batch script:
- `./scripts/generate_timelapses.sh` generates videos for all dates under `BASE_DIR`.
- Add `--missing-only` to rebuild only days missing timelapse output.

```shell
./scripts/generate_timelapses.sh
```
```shell
./scripts/generate_timelapses.sh --fps 24
```
```shell
./scripts/generate_timelapses.sh --missing-only
```
```shell
./scripts/generate_timelapses.sh --overwrite --delete
```
```shell
./scripts/generate_timelapses.sh --base-dir "$HOME/Documents/Screenshots"
```

## Make Targets

- Single date:
  - `make timelapse DATE=YYYY-MM-DD [FPS=30] [BASE_DIR=~/Documents/Screenshots] [OVERWRITE=true] [DELETE=true]`
- All dates:
  - `make timelapses [FPS=30] [BASE_DIR=~/Documents/Screenshots] [OVERWRITE=true] [DELETE=true] [MISSING_ONLY=true]`

```shell
make timelapse DATE=2025-10-21
```
```shell
make timelapse DATE=2025-10-21 FPS=24 OVERWRITE=true
```
```shell
make timelapses
```
```shell
make timelapses MISSING_ONLY=true
```
```shell
make timelapses FPS=24 BASE_DIR="$HOME/Documents/Screenshots" DELETE=true
```

Notes:
- `OVERWRITE=true` includes `--overwrite`; `DELETE=true` includes `--delete`.
- `MISSING_ONLY=true` includes `--missing-only` to process only dates missing output.
- `BASE_DIR` and `FPS` default to the values shown.

## Requirements

- Python 3.x
- ffmpeg (macOS: `brew install ffmpeg`)

- To set up your environment, run `make deps`.
This command will install all required dependencies using pip.
If you need to upgrade any of these dependencies, simply re-run this command.

## Building the package

To build the SnapSpan package, run `make package`.
This will create a tarball of the project in the `dist` directory.

## Contributing

Contributions are welcome! Please create a new issue to discuss changes or propose new features.

## License

SnapSpan is released under the MIT License.
