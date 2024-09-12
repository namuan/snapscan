import rumps
from screeninfo import get_monitors
from mss import mss
from pathlib import Path
from datetime import datetime
from PIL import Image
import threading
import time
import numpy as np
import logging
import subprocess


def setup_logger():
    user_home = Path.home()
    log_dir = user_home / ".logs" / "snap_scan"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"snap_scan_{datetime.now().strftime('%Y%m%d')}.log"

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove all existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create file handler
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class ScreenshotApp(rumps.App):
    def __init__(self):
        super(ScreenshotApp, self).__init__("📷")
        self.menu = [
            "Take Screenshot Now",
            None,
            rumps.MenuItem("Stop Scheduling", callback=self.toggle_scheduling),
            None,
            "Open Screenshots Folder",
        ]
        self.scheduling_thread = None
        self.is_scheduling = False
        self.stop_event = threading.Event()
        self.previous_screenshot = None
        setup_logger()  # Set up the logger
        self.start_scheduling()

    @staticmethod
    def get_screenshot_path():
        now = datetime.now()
        base_path = Path.home() / "Documents" / "Screenshots"
        path = base_path / now.strftime("%Y/%m/%d")
        path.mkdir(parents=True, exist_ok=True)
        return path, now.strftime("%Y%m%d_%H%M%S")

    @rumps.clicked("Take Screenshot Now")
    def take_screenshot(self, _):
        self.capture_screenshot(force_save=True)

    @rumps.clicked("Open Screenshots Folder")
    def open_screenshots_folder(self, _):
        base_path = Path.home() / "Documents" / "Screenshots"
        subprocess.run(["open", str(base_path)])
        logging.info(f"Opened screenshots folder: {base_path}")

    def capture_screenshot(self, force_save=False):
        monitors = get_monitors()
        num_monitors = len(monitors)
        logging.info(f"Number of monitors detected: {num_monitors}")

        screenshots = []
        max_width = 0
        max_height = 0
        with mss() as sct:
            for i, monitor in enumerate(
                sct.monitors[1:], 1
            ):  # Skip the first monitor (entire screen)
                screenshot = sct.grab(monitor)
                img = Image.frombytes(
                    "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
                )
                screenshots.append(img)
                max_width = max(max_width, img.width)
                max_height = max(max_height, img.height)
                logging.info(f"Screenshot captured for monitor {i}")

        if num_monitors > 1:
            # Scale up images to match the highest resolution
            scaled_screenshots = []
            for img in screenshots:
                if img.width != max_width or img.height != max_height:
                    scale_factor = max(max_width / img.width, max_height / img.height)
                    new_size = (
                        int(img.width * scale_factor),
                        int(img.height * scale_factor),
                    )
                    scaled_img = img.resize(new_size, Image.LANCZOS)
                    scaled_screenshots.append(scaled_img)
                else:
                    scaled_screenshots.append(img)

            # Stitch images together
            total_width = sum(img.width for img in scaled_screenshots)
            current_screenshot = Image.new("RGB", (total_width, max_height))
            x_offset = 0
            for img in scaled_screenshots:
                current_screenshot.paste(img, (x_offset, 0))
                x_offset += img.width
        else:
            current_screenshot = screenshots[0]

        if force_save or self.has_screen_changed(current_screenshot):
            path, timestamp = self.get_screenshot_path()
            filename = path / f"{timestamp}.png"

            # Save the PNG with optimization
            current_screenshot.save(
                str(filename), format="PNG", optimize=True, compress_level=9
            )

            logging.info(f"Screenshot saved: {filename}")
            logging.info(f"File size: {filename.stat().st_size / 1024:.2f} KB")
            self.previous_screenshot = current_screenshot
        else:
            logging.info("No changes detected, screenshot not saved.")

    def has_screen_changed(self, current_screenshot):
        if self.previous_screenshot is None:
            return True

        # Convert images to numpy arrays for comparison
        current_array = np.array(current_screenshot)
        previous_array = np.array(self.previous_screenshot)

        # Check if the shapes are different (which would indicate a change)
        if current_array.shape != previous_array.shape:
            return True

        # Calculate the difference between the two arrays
        diff = np.abs(current_array - previous_array)

        # If the maximum difference is above a threshold, consider it changed
        # You can adjust this threshold as needed
        return np.max(diff) > 10

    def scheduled_task(self):
        while not self.stop_event.is_set():
            self.capture_screenshot()
            # Wait for 60 seconds or until the stop event is set
            self.stop_event.wait(timeout=60)

    def toggle_scheduling(self, sender):
        if not self.is_scheduling:
            self.start_scheduling()
            sender.title = "Stop Scheduling (Active)"
        else:
            self.stop_scheduling()
            sender.title = "Start Scheduling"

    def start_scheduling(self):
        if not self.is_scheduling:
            self.is_scheduling = True
            self.stop_event.clear()
            self.scheduling_thread = threading.Thread(target=self.scheduled_task)
            self.scheduling_thread.start()
            logging.info("Scheduling started")
            rumps.notification(
                "Screenshot Scheduler",
                "Scheduling Started",
                "Screenshots will be taken every minute",
            )

    def stop_scheduling(self):
        if self.is_scheduling:
            self.is_scheduling = False
            self.stop_event.set()
            logging.info("Scheduling stopped")
            rumps.notification(
                "Screenshot Scheduler",
                "Scheduling Stopped",
                "Screenshot scheduling has been stopped",
            )

    def terminate(self):
        self.stop_scheduling()
        super().terminate()


if __name__ == "__main__":
    setup_logger()
    logging.info("Starting ScreenshotApp")
    ScreenshotApp().run()
