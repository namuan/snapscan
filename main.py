import rumps
from screeninfo import get_monitors
from mss import mss
import os
from datetime import datetime
from PIL import Image
import threading
import time

class ScreenshotApp(rumps.App):
    def __init__(self):
        super(ScreenshotApp, self).__init__("📷")
        self.menu = ["Take Screenshot Now",
                     None,  # This adds a separator line in the menu
                     rumps.MenuItem("Start Scheduling", callback=self.start_scheduling),
                     rumps.MenuItem("Stop Scheduling", callback=self.stop_scheduling),
                     None]  # This adds another separator line before Quit
        self.scheduling_thread = None
        self.is_scheduling = False

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
        self.capture_screenshot()

    def capture_screenshot(self):
        monitors = get_monitors()
        num_monitors = len(monitors)
        print(f"Number of monitors detected: {num_monitors}")

        screenshots = []
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):  # Skip the first monitor (entire screen)
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                screenshots.append(img)
                print(f"Screenshot captured for monitor {i}")

        path, timestamp = self.get_screenshot_path()
        filename = os.path.join(path, f"{timestamp}.png")

        if num_monitors > 1:
            # Stitch images together
            total_width = sum(img.width for img in screenshots)
            max_height = max(img.height for img in screenshots)

            stitched_image = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for img in screenshots:
                stitched_image.paste(img, (x_offset, 0))
                x_offset += img.width

            # Save the stitched image
            stitched_image.save(filename)
            print(f"Stitched screenshot saved: {filename}")
        else:
            # Save single monitor screenshot
            screenshots[0].save(filename)
            print(f"Single monitor screenshot saved: {filename}")

    def scheduled_task(self):
        while self.is_scheduling:
            self.capture_screenshot()
            time.sleep(60)  # Wait for 60 seconds

    def start_scheduling(self, _):
        if not self.is_scheduling:
            self.is_scheduling = True
            self.scheduling_thread = threading.Thread(target=self.scheduled_task)
            self.scheduling_thread.start()
            print("Scheduling started")
            rumps.notification("Screenshot Scheduler", "Scheduling Started", "Screenshots will be taken every minute")

    def stop_scheduling(self, _):
        if self.is_scheduling:
            self.is_scheduling = False
            if self.scheduling_thread:
                self.scheduling_thread.join()
            print("Scheduling stopped")
            rumps.notification("Screenshot Scheduler", "Scheduling Stopped", "Screenshot scheduling has been stopped")

if __name__ == "__main__":
    ScreenshotApp().run()