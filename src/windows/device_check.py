"""Side window for automatic device and driver detection."""

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from checks.devices import check_devices
from theme import COLORS


def device_check_window(root):
    win = tk.Toplevel(root)
    win.title("Device and driver check")
    win.geometry("560x440")

    tk.Label(
        win,
        text="Device detection",
        font=("sans", 15, "bold"),
        padx=12,
        pady=10,
    ).pack(anchor="w")
    tk.Label(
        win,
        text="Presence checks cannot confirm operation. Follow up with functional tests.",
        justify="left",
        wraplength=530,
        padx=12,
    ).pack(anchor="w", pady=(0, 8))

    status_label = tk.Label(
        win,
        text="Starting scan...",
        font=("sans", 11, "bold"),
        fg="white",
        bg=COLORS["info"],
        pady=6,
    )
    status_label.pack(fill="x", padx=12)
    output = scrolledtext.ScrolledText(win, font=("monospace", 10), wrap="word")
    output.pack(fill="both", expand=True, padx=12, pady=8)
    output.insert("end", "Checking input devices, audio, and PCI/USB drivers...")
    output.configure(state="disabled")

    results = queue.Queue()

    def scan():
        scan_button.configure(state="disabled")
        status_label.configure(text="Scanning...", bg=COLORS["info"])

        def worker():
            try:
                results.put(check_devices())
            except Exception as error:
                results.put(("fail", f"Unexpected error:\n{type(error).__name__}: {error}"))

        threading.Thread(target=worker, daemon=True).start()
        win.after(100, poll)

    def poll():
        try:
            status, report = results.get_nowait()
        except queue.Empty:
            win.after(100, poll)
            return
        status_label.configure(
            text={
                "warn": "Further testing needed",
                "fail": "Scan failed",
                "info": "Detection complete",
            }.get(status, "Scan complete"),
            bg=COLORS.get(status, COLORS["info"]),
        )
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("end", report)
        output.configure(state="disabled")
        scan_button.configure(state="normal")

    scan_button = tk.Button(win, text="Rescan", command=scan)
    scan_button.pack(anchor="e", padx=12, pady=(0, 12))
    scan()
    win.focus_force()