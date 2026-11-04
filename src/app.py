"""Main window: test buttons on the left, status badge and output on the right."""

import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext

from checks.battery import check_battery
from checks.speakers import play_speakers
from checks.system import check_summary, check_usb, shutdown_system
from checks.webcam import check_webcam
from theme import COLORS
from windows.keyboard import keyboard_window
from windows.mouse import mouse_window
from windows.screen import screen_window
from windows.webcam import webcam_window

# Checks that run together under "Run all quick checks".
QUICK_CHECKS = [
    ("Summary", check_summary),
    ("Battery", check_battery),
    ("Webcam", check_webcam),
    ("USB", check_usb),
]


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
        self.results = {}
        self.q = queue.Queue()
        root.title("Quick Hardware Test")
        root.geometry("860x680")

        left = tk.Frame(root, padx=10, pady=10)
        left.pack(side="left", fill="y")
        right = tk.Frame(root, padx=10, pady=10)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="Tests", font=("sans", 14, "bold")).pack(anchor="w")
        buttons = [
            ("Battery health", lambda: self.go("Battery", check_battery)),
            ("Keyboard (lights up)", lambda: keyboard_window(root)),
            ("Mouse / touchpad", lambda: mouse_window(root)),
            ("Speakers (MP3)", lambda: self.go("Speakers", play_speakers)),
            ("Webcam (live preview)", lambda: webcam_window(root)),
            ("USB devices", lambda: self.go("USB", check_usb)),
            ("Screen colours", lambda: screen_window(root)),
            ("System summary", lambda: self.go("Summary", check_summary)),
        ]
        for text, cmd in buttons:
            tk.Button(left, text=text, width=22, pady=4, command=cmd).pack(pady=2)
        tk.Button(
            left, text="Run all quick checks", width=22, pady=4,
            bg="#1565c0", fg="white", command=self.run_all,
        ).pack(pady=(12, 2))
        tk.Button(
            left, text="Save report", width=22, pady=4, command=self.save
        ).pack(pady=2)
        tk.Button(
            left, text="Shutdown", width=22, pady=4, command=self.shutdown
        ).pack(pady=10)

        self.badge = tk.Label(
            right, text="Ready", font=("sans", 18, "bold"),
            fg="white", bg=COLORS["info"], pady=8,
        )
        self.badge.pack(fill="x")
        self.out = scrolledtext.ScrolledText(right, font=("monospace", 11), wrap="word")
        self.out.pack(fill="both", expand=True, pady=(8, 0))
        root.after(100, self.poll)

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

    # ---- background work (workers only touch the queue, never widgets)

    def go(self, title, fn):
        self.badge.config(text=f"{title}: running...", bg=COLORS["info"])

        def worker():
            try:
                status, text = fn()
            except Exception as e:
                status, text = "fail", f"Unexpected error:\n{type(e).__name__}: {e}"
            self.q.put((title, status, text))

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                title, status, text = self.q.get_nowait()
                if title != "Overall":
                    self.results[title] = (status, text)
                self.show(status, text, title)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def run_all(self):
        self.badge.config(text="Running all checks...", bg=COLORS["info"])

        def worker():
            collected = {}
            for title, fn in QUICK_CHECKS:
                try:
                    collected[title] = fn()
                except Exception as e:
                    collected[title] = ("fail", f"Unexpected error:\n{type(e).__name__}: {e}")
                # Store each result so Save report includes it
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

    def save(self):
        if not self.results:
            messagebox.showinfo("Nothing to save", "Run some tests first, then save the report.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"hwtest-{datetime.now():%Y%m%d-%H%M%S}.txt",
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                f.write(f"Hardware test report - {datetime.now():%Y-%m-%d %H:%M}\n\n")
                for title, (status, text) in self.results.items():
                    f.write(f"[{status.upper()}] {title}\n{text}\n\n")
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return
        messagebox.showinfo("Saved", f"Report saved to:\n{path}")
