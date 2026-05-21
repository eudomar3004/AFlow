import subprocess
import time
from typing import Optional

_active_app: Optional[str] = None


def save_frontmost_app():
    global _active_app
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=2,
        )
        name = result.stdout.strip()
        if name and name != "AFlow":
            _active_app = name
    except Exception:
        pass


def paste_text(text: str):
    global _active_app

    # Copy to clipboard — use NSPasteboard for correct UTF-8 in .app bundles
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSPasteboardTypeString)
    except Exception:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)

    # Restore focus to the app active before recording
    if _active_app:
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "{_active_app}" to activate'],
                timeout=2, check=True,
            )
            time.sleep(0.12)
        except Exception:
            pass

    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "v" using command down'],
        check=True,
    )
    _active_app = None
