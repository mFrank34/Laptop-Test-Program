"""Quick camera presence check (the live preview is in windows/webcam.py)."""

import glob


def check_webcam():
    cams = glob.glob("/dev/video*")
    if not cams:
        return "fail", "No camera detected."
    return "pass", "Camera device(s): " + ", ".join(sorted(cams))
