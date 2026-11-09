"""Application log viewer window."""

import tkinter as tk
from tkinter import scrolledtext

from windows.window_size import fit_window


def program_log_window(root, log_path):
    win = tk.Toplevel(root)
    win.title("Program log")
    window_width, _window_height = fit_window(
        win, 760, 520, min_width=560, min_height=360
    )

    tk.Label(
        win,
        text=f"Log file: {log_path}",
        font=("sans", 10),
        anchor="w",
        justify="left",
        wraplength=max(240, window_width - 30),
    ).pack(fill="x", padx=10, pady=(10, 4))
    output = scrolledtext.ScrolledText(win, font=("monospace", 10), wrap="word")
    output.pack(fill="both", expand=True, padx=10, pady=4)

    def refresh():
        try:
            with open(log_path, encoding="utf-8", errors="replace") as log_file:
                lines = log_file.readlines()
            text = "".join(lines[-3000:]) or "Log is empty."
        except OSError as error:
            text = f"Could not read log:\n{error}"
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("end", text)
        output.see("end")
        output.configure(state="disabled")

    controls = tk.Frame(win)
    controls.pack(fill="x", padx=10, pady=(4, 10))
    tk.Button(controls, text="Refresh", command=refresh).pack(side="left")
    refresh()