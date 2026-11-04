#!/usr/bin/env python3
"""Quick Hardware Test - entry point.

Run:  python3 main.py      (use sudo for the serial number and the raw key listener)
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from app import App


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()