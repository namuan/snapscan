import AppKit
from Quartz import (CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly,
                    kCGNullWindowID, CGWindowListCreateDescriptionFromArray)

def get_window_names():
    window_names = []

    # Get the currently active application
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    active_app = workspace.activeApplication()
    active_app_name = active_app['NSApplicationName']

    # Get all windows
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

    for window in window_list:
        app_name = window.get('kCGWindowOwnerName', '<< no name >>')
        window_name = window.get('kCGWindowName', '<< no title >>')

        if window_name:
            window_names.append(f"{app_name}: {window_name}")

    return window_names, active_app_name

# Get and print all window names
window_names, active_app = get_window_names()

print("All windows:")
for name in window_names:
    print(name)

print(f"Currently active application: {active_app}\n")
