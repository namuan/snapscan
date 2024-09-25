import AppKit
from Quartz import (CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
                    kCGNullWindowID)
import json
import time
from datetime import datetime

def get_window_info():
    # Get the currently active application
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    active_app = workspace.activeApplication()
    active_app_name = active_app['NSApplicationName']

    # Get all windows
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

    # Find the active window
    active_window_name = "Unknown"
    window_info = []

    for window in window_list:
        app_name = window.get('kCGWindowOwnerName', 'Unknown')
        window_name = window.get('kCGWindowName', 'Untitled')

        if app_name == active_app_name and window_name:
            active_window_name = window_name

        if window_name:
            window_info.append({
                "app_name": app_name,
                "window_name": window_name,
                "is_active": app_name == active_app_name
            })

    return {
        "timestamp": datetime.now().isoformat(),
        "active_app": {
            "name": active_app_name,
            "window": active_window_name
        },
        "windows": window_info
    }

def save_to_file(data, filename):
    with open(filename, 'a') as f:
        json.dump(data, f)
        f.write('\n')  # Add newline to separate entries

window_data = get_window_info()
save_to_file(window_data, 'window_data.jsonl')
