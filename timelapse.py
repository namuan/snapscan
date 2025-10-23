#!/usr/bin/env python3
"""
Timelapse generator for SnapSpan screenshots.

Generates an MP4 time-lapse video for a given date from screenshots stored
under ~/Documents/Screenshots/YYYY/MM/DD (default), as created by main.py.

Requires ffmpeg to be installed and available on PATH.

Usage examples:
  python timelapse.py --date 2025-10-21
  python timelapse.py --date 2025-10-21 --fps 24 --overwrite
  python timelapse.py --date 2025-10-21 --delete
  python timelapse.py --date 2025-10-21 --base-dir /custom/Screenshots --output /tmp/out.mp4
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a time-lapse MP4 from screenshots for a given date",
    )
    parser.add_argument(
        "--date",
        "-d",
        help="Date in YYYY-MM-DD format (defaults to today)",
        default=None,
    )
    parser.add_argument(
        "--base-dir",
        "-b",
        help="Base screenshots directory",
        default=str(Path.home() / "Documents" / "Screenshots"),
    )
    parser.add_argument(
        "--fps",
        "-r",
        type=int,
        default=30,
        help="Frames per second for the output video",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output MP4 file path (defaults inside the date folder)",
        default=None,
    )
    parser.add_argument(
        "--overwrite",
        "-y",
        action="store_true",
        help="Overwrite output file if it exists",
    )
    parser.add_argument(
        "--skip-if-existing",
        action="store_true",
        help="Skip generation if the output file already exists",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete screenshots after successful video generation",
    )
    return parser.parse_args()


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        print(
            "Error: ffmpeg is not installed or not found on PATH.\n"
            "Install it (e.g., on macOS: brew install ffmpeg) and try again.",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_date(date_str: str | None) -> date:
    if not date_str:
        return datetime.today().date()
    # Try flexible parsing; default to strict format if needed
    try:
        # Support both YYYY-MM-DD and YYYYMMDD
        if "-" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        print("Date must be in YYYY-MM-DD or YYYYMMDD format", file=sys.stderr)
        sys.exit(2)


def build_date_dir(base_dir: Path, d: date) -> Path:
    return base_dir / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}"


def find_images(date_dir: Path) -> list[Path]:
    if not date_dir.exists():
        print(f"No directory found for date: {date_dir}", file=sys.stderr)
        sys.exit(3)
    # PNG screenshots produced by the app; ignore JSONL metadata
    images = sorted([p for p in date_dir.iterdir() if p.suffix.lower() == ".png"])
    return images


def default_output_path(date_dir: Path, d: date) -> Path:
    return date_dir / f"timelapse-{d.strftime('%Y%m%d')}.mp4"


def prepare_sequence_symlinks(images: list[Path], tmpdir: Path) -> Path:
    """
    Create a numeric sequence of symlinks (000000.png, 000001.png, ...) pointing
    to the original images to guarantee a deterministic order for ffmpeg.
    """
    for idx, src in enumerate(images):
        dest = tmpdir / f"{idx:06d}.png"
        try:
            dest.symlink_to(src.resolve())
        except (OSError, NotImplementedError):
            # Fallback to copying if symlink is not permitted
            shutil.copy2(src, dest)
    return tmpdir / "%06d.png"


def run_ffmpeg(sequence_pattern: Path, fps: int, output: Path, overwrite: bool) -> int:
    # Ensure parent folder exists
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-framerate",
        str(fps),
        "-i",
        str(sequence_pattern),
        # Make sure video dimensions are even for H.264
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode or 6


def main() -> None:
    args = parse_args()
    ensure_ffmpeg_available()

    d = parse_date(args.date)
    base_dir = Path(args.base_dir).expanduser()
    date_dir = build_date_dir(base_dir, d)

    images = find_images(date_dir)
    if not images:
        print(f"{d.isoformat()} - skipped: no screenshots in {date_dir}")
        sys.exit(0)

    output = (
        Path(args.output).expanduser()
        if args.output
        else default_output_path(date_dir, d)
    )

    if output.exists() and not args.overwrite:
        if args.skip_if_existing:
            print(f"{d.isoformat()} - skipped: output exists ({output})")
        else:
            print(
                f"{d.isoformat()} - skipped: output exists ({output}); use --overwrite"
            )
        sys.exit(0)

    with tempfile.TemporaryDirectory(prefix="snapspan-frames-") as t:
        tmpdir = Path(t)
        sequence_pattern = prepare_sequence_symlinks(images, tmpdir)
        exit_code = run_ffmpeg(
            sequence_pattern, args.fps, output, overwrite=args.overwrite
        )

    if exit_code == 0:
        if args.delete:
            deleted = 0
            for p in images:
                try:
                    p.unlink()
                    deleted += 1
                except OSError:
                    # Keep one-line status; warn via stderr without breaking the summary
                    print(f"Warning: failed to delete {p}", file=sys.stderr)
            print(
                f"{d.isoformat()} - generated: {output} (deleted {deleted} screenshots)"
            )
        else:
            print(f"{d.isoformat()} - generated: {output}")
        sys.exit(0)
    else:
        print(f"{d.isoformat()} - failed: ffmpeg exit {exit_code} for {output}")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
