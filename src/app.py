"""Main window: test buttons on the left, status badge and output on the right."""

import os
import queue
import re
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from checks.battery import check_battery
from checks.speakers import play_speakers
from checks.system import (
    added_usb_devices,
    check_summary,
    check_usb,
    play_usb_chime,
    shutdown_system,
)
from checks.drives import check_drives
from checks.devices import check_devices
from checks.webcam import check_webcam
from app_log import configure_logging
from theme import COLORS
from windows.keyboard import keyboard_window
from windows.trackpad import trackpad_window
from windows.device_check import device_check_window
from windows.screen import screen_window
from windows.webcam import webcam_window
from windows.program_log import program_log_window
from windows.touchscreen import touchscreen_window

# Checks that run together under "Run all quick checks".
QUICK_CHECKS = [
    ("Summary", check_summary),
    ("Battery", check_battery),
    ("Drives", check_drives),
    ("Webcam", check_webcam),
    ("USB", check_usb),
    ("Devices / drivers", check_devices),
]


def format_usb_device(line):
    """'Bus 001 Device 004: ID 0781:5567 SanDisk Corp. Cruzer' -> 'SanDisk Corp. Cruzer  (0781:5567)'"""
    m = re.match(r"Bus \d+ Device \d+: ID (\w{4}:\w{4})\s*(.*)$", line.strip())
    if not m:
        return line.strip()
    ids, name = m.groups()
    return f"{name or 'Unknown device'}  ({ids})"


def worst_status(statuses):
    worst = "pass"
    for status in statuses:
        if status == "fail":
            return "fail"
        if status == "warn":
            worst = "warn"
    return worst


class App:
    def __init__(self, root):
        self.root = root
        self.logger, self.log_path = configure_logging()
        self.logger.info("Application started")
        self.results = {}
        self.q = queue.Queue()
        root.title("Quick Hardware Test")
        root.geometry("860x680")

        log_panel = tk.Frame(root, padx=10, pady=8)
        log_panel.pack(side="bottom", fill="x")
        tk.Button(
            log_panel,
            text="Program log",
            command=lambda: program_log_window(root, self.log_path),
        ).pack(side="right")

        left = tk.Frame(root, padx=10, pady=10)
        left.pack(side="left", fill="y")
        right = tk.Frame(root, padx=10, pady=10)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="Tests", font=("sans", 14, "bold")).pack(anchor="w")
        buttons = [
            ("Battery health", lambda: self.go("Battery", check_battery)),
            ("Keyboard (lights up)", lambda: keyboard_window(root)),
            ("Trackpad test", lambda: trackpad_window(root)),
            ("Speakers (MP3)", lambda: self.go("Speakers", play_speakers)),
            ("Webcam (live preview)", lambda: webcam_window(root)),
            ("USB devices", lambda: self.go("USB", check_usb)),
            ("Devices / drivers", lambda: device_check_window(root)),
            ("Drives / storage", lambda: self.go("Drives", check_drives)),
            ("Screen colours", lambda: screen_window(root)),
            ("Touchscreen test", lambda: touchscreen_window(root)),
            ("System summary", lambda: self.go("Summary", check_summary)),
        ]
        for text, cmd in buttons:
            tk.Button(left, text=text, width=22, pady=4, command=cmd).pack(pady=2)
        tk.Button(
            left,
            text="Run all quick checks",
            width=22,
            pady=4,
            bg="#1565c0",
            fg="white",
            command=self.run_all,
        ).pack(pady=(12, 2))
        tk.Button(left, text="Shutdown", width=22, pady=4, command=self.shutdown).pack(
            pady=10
        )

        self.badge = tk.Label(
            right,
            text="Ready",
            font=("sans", 18, "bold"),
            fg="white",
            bg=COLORS["info"],
            pady=8,
        )
        self.badge.pack(fill="x")
        self.out = scrolledtext.ScrolledText(right, font=("monospace", 11), wrap="word")
        self.out.pack(fill="both", expand=True, pady=(8, 0))
        root.after(100, self.poll)
        self.usb_monitor_stop = threading.Event()
        self.usb_popup = None
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.report_callback_exception = self.report_callback_exception
        threading.Thread(target=self.monitor_usb, daemon=True).start()

        if os.geteuid() != 0:
            self.show("info", "Tip: run with sudo for the serial number.")

    # ---- display

    def show(self, status, text, title=""):
        self.badge.config(
            text=(title + "  " if title else "") + status.upper(),
            bg=COLORS.get(status, COLORS["info"]),
        )
        self.out.delete("1.0", "end")
        self.out.insert("end", text)

    def report_callback_exception(self, exception, value, traceback):
        self.logger.error(
            "Unhandled GUI callback exception",
            exc_info=(exception, value, traceback),
        )

    # ---- background work (workers only touch the queue, never widgets)

    def go(self, title, fn):
        self.badge.config(text=f"{title}: running...", bg=COLORS["info"])

        def worker():
            self.logger.info("Check started: %s", title)
            try:
                status, text = fn()
            except Exception as e:
                self.logger.exception("Check failed: %s", title)
                status, text = "fail", f"Unexpected error:\n{type(e).__name__}: {e}"
            self.logger.info("Check finished: %s [%s]", title, status)
            self.q.put((title, status, text))

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                title, status, text = self.q.get_nowait()
                if title == "!usb":
                    self.show_usb_popup(text.splitlines())
                    continue
                if title != "Overall":
                    self.results[title] = (status, text)
                self.show(status, text, title)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def monitor_usb(self):
        try:
            status, snapshot = check_usb()
        except Exception:
            self.logger.exception("USB device monitor failed")
            status, snapshot = "warn", ""
        previous = set(snapshot.splitlines()) if status != "warn" else None
        while not self.usb_monitor_stop.wait(2):
            try:
                status, snapshot = check_usb()
            except Exception:
                self.logger.exception("USB device monitor failed")
                continue
            if status == "warn":
                continue
            current = set(snapshot.splitlines())
            if previous is not None:
                added = added_usb_devices("\n".join(previous), snapshot)
                if added:
                    details = "New USB device connected:\n" + "\n".join(added)
                    details += "\n\nConnected USB devices:\n" + (
                        snapshot or "None detected"
                    )
                    self.q.put(("USB", "info", details))
                    self.q.put(
                        ("!usb", "info", "\n".join(format_usb_device(d) for d in added))
                    )
                    play_usb_chime()
            previous = current

    def show_usb_popup(self, devices):
        """Small window naming the USB device(s) just plugged in. Closes itself after a few seconds."""
        self.close_usb_popup()
        win = tk.Toplevel(self.root)
        win.withdraw()  # build it hidden, show it once it is positioned (no jump)
        self.usb_popup = win
        win.title("USB device connected")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        tk.Label(
            win,
            text="USB device connected",
            font=("sans", 14, "bold"),
            fg="white",
            bg=COLORS["pass"],
            padx=24,
            pady=8,
        ).pack(fill="x")
        tk.Label(
            win,
            text="\n".join(devices),
            font=("sans", 11),
            justify="left",
            padx=24,
            pady=14,
        ).pack()
        tk.Button(win, text="OK", width=10, command=self.close_usb_popup).pack(
            pady=(0, 14)
        )

        # centre it over the main window
        win.update_idletasks()
        x = (
            self.root.winfo_rootx()
            + (self.root.winfo_width() - win.winfo_reqwidth()) // 2
        )
        y = (
            self.root.winfo_rooty()
            + (self.root.winfo_height() - win.winfo_reqheight()) // 2
        )
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.deiconify()
        self.root.after(6000, self.close_usb_popup, win)

    def close_usb_popup(self, only=None):
        """Close the pop-up. If `only` is given, close it only if it is still the current one."""
        win = self.usb_popup
        if win is None or (only is not None and win is not only):
            return
        self.usb_popup = None
        try:
            win.destroy()
        except tk.TclError:
            pass

    def close(self):
        self.logger.info("Application closing")
        self.usb_monitor_stop.set()
        self.root.destroy()

    def run_all(self):
        self.badge.config(text="Running all checks...", bg=COLORS["info"])

        def worker():
            collected = {}
            for title, fn in QUICK_CHECKS:
                self.logger.info("Quick check started: %s", title)
                try:
                    collected[title] = fn()
                except Exception as e:
                    self.logger.exception("Quick check failed: %s", title)
                    collected[title] = (
                        "fail",
                        f"Unexpected error:\n{type(e).__name__}: {e}",
                    )
                self.logger.info(
                    "Quick check finished: %s [%s]",
                    title,
                    collected[title][0],
                )
                # Show each result as it completes
                self.q.put((title, *collected[title]))
            lines = [
                f"[{status.upper()}] {title}\n{text}\n"
                for title, (status, text) in collected.items()
            ]
            worst = worst_status(status for status, _ in collected.values())
            self.q.put(("Overall", worst, "\n".join(lines)))

        threading.Thread(target=worker, daemon=True).start()

    # ---- actions

    def shutdown(self):
        if messagebox.askyesno("Shutdown", "Power off this computer now?"):
            self.go("Shutdown", shutdown_system)
