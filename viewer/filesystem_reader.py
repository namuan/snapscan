from pathlib import Path
from datetime import date as Date
from typing import List, Optional
import logging


class FileSystemReader:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.last_error_msg: Optional[str] = None

    def get_available_dates(self) -> List[Date]:
        results: List[Date] = []
        self.last_error_msg = None
        if not self.validate_base_directory():
            return results
        try:
            for year_dir in sorted(self.base_path.iterdir()):
                if not year_dir.is_dir():
                    continue
                if not year_dir.name.isdigit() or len(year_dir.name) != 4:
                    continue
                for month_dir in sorted(year_dir.iterdir()):
                    if not month_dir.is_dir():
                        continue
                    if not month_dir.name.isdigit() or len(month_dir.name) != 2:
                        continue
                    for day_dir in sorted(month_dir.iterdir()):
                        if not day_dir.is_dir():
                            continue
                        if not day_dir.name.isdigit() or len(day_dir.name) != 2:
                            continue
                        try:
                            y = int(year_dir.name)
                            m = int(month_dir.name)
                            d = int(day_dir.name)
                            results.append(Date(y, m, d))
                        except ValueError:
                            continue
        except PermissionError as e:
            self.last_error_msg = f"Permission denied: {self.base_path}"
            logging.error("Permission error scanning base directory: %s", e)
        except OSError as e:
            self.last_error_msg = str(e)
            logging.error("OS error scanning base directory: %s", e)
        return sorted(results)

    def get_video_path(self, d: Date) -> Optional[Path]:
        try:
            date_dir = (
                self.base_path / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}"
            )
            video_name = f"timelapse-{d.strftime('%Y%m%d')}.mp4"
            p = date_dir / video_name
            return p if p.exists() and p.is_file() else None
        except PermissionError as e:
            self.last_error_msg = f"Permission denied: {date_dir}"
            logging.error("Permission error accessing video path: %s", e)
            return None

    def video_exists(self, d: Date) -> bool:
        return self.get_video_path(d) is not None

    def get_window_data_path(self, d: Date) -> Optional[Path]:
        try:
            date_dir = (
                self.base_path / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}"
            )
            p = date_dir / "window_data.jsonl"
            return p if p.exists() and p.is_file() else None
        except PermissionError as e:
            self.last_error_msg = f"Permission denied: {date_dir}"
            logging.error("Permission error accessing window data path: %s", e)
            return None

    def validate_base_directory(self) -> bool:
        return self.base_path.exists() and self.base_path.is_dir()
