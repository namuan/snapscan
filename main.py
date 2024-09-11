import rumps
from screeninfo import get_monitors
from mss import mss
import os
from datetime import datetime
from PIL import Image
import threading
import time
import numpy as np


class ScreenshotApp(rumps.App):
    def __init__(self):
        super(ScreenshotApp, self).__init__("📷")
        self.menu = [
            "Take Screenshot Now",
            None,  # This adds a separator line in the menu
            rumps.MenuItem("Start Scheduling", callback=self.toggle_scheduling),
            None  # This adds another separator line before Quit
        ]
        self.scheduling_thread = None
        self.is_scheduling = False
        self.stop_event = threading.Event()
        self.previous_screenshot = None

    def get_screenshot_path(self):
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        timestamp = now.strftime('%Y%m%d_%H%M%S')

        path = os.path.join("screenshots", year, month, day)
        os.makedirs(path, exist_ok=True)

        return path, timestamp

    @rumps.clicked("Take Screenshot Now")
    def take_screenshot(self, _):
        self.capture_screenshot(force_save=True)

    def capture_screenshot(self, force_save=False):
        monitors = get_monitors()
        num_monitors = len(monitors)
        print(f"Number of monitors detected: {num_monitors}")

        screenshots = []
        max_width = 0
        max_height = 0
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):  # Skip the first monitor (entire screen)
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                screenshots.append(img)
                max_width = max(max_width, img.width)
                max_height = max(max_height, img.height)
                print(f"Screenshot captured for monitor {i}")

        if num_monitors > 1:
            # Scale up images to match the highest resolution
            scaled_screenshots = []
            for img in screenshots:
                if img.width != max_width or img.height != max_height:
                    scale_factor = max(max_width / img.width, max_height / img.height)
                    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                    scaled_img = img.resize(new_size, Image.LANCZOS)
                    scaled_screenshots.append(scaled_img)
                else:
                    scaled_screenshots.append(img)

            # Stitch images together
            total_width = sum(img.width for img in scaled_screenshots)
            current_screenshot = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for img in scaled_screenshots:
                current_screenshot.paste(img, (x_offset, 0))
                x_offset += img.width
        else:
            current_screenshot = screenshots[0]

        if force_save or self.has_screen_changed(current_screenshot):
            path, timestamp = self.get_screenshot_path()
            filename = os.path.join(path, f"{timestamp}.png")
            current_screenshot.save(filename)
            print(f"Screenshot saved: {filename}")
            self.previous_screenshot = current_screenshot
        else:
            print("No changes detected, screenshot not saved.")

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
            print("Scheduling started")
            rumps.notification("Screenshot Scheduler", "Scheduling Started", "Screenshots will be taken every minute")

    def stop_scheduling(self):
        if self.is_scheduling:
            self.is_scheduling = False
            self.stop_event.set()
            print("Scheduling stopped")
            rumps.notification("Screenshot Scheduler", "Scheduling Stopped", "Screenshot scheduling has been stopped")

    def terminate(self):
        self.stop_scheduling()
        super().terminate()


if __name__ == "__main__":
    ScreenshotApp().run()
