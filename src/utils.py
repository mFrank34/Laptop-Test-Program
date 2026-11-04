"""Small helpers shared by checks and windows. No GUI code here."""

import os
import subprocess
import sys


def read(path):
    """Return the stripped text of a file, or None if it can't be read."""
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def run(cmd, timeout=15):
    """Run a command. Returns (return_code, combined_output)."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.returncode, (out.stdout + out.stderr).strip()
    except FileNotFoundError:
        return 127, f"'{cmd[0]}' is not installed"
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def app_dir():
    """Project root (the folder above src/), also when frozen."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))