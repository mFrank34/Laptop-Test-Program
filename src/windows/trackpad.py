"""Trackpad gesture tester using desktop pointer events."""

import tkinter as tk

from checks.devices import detect_input_devices
from theme import COLORS


def trackpad_window(root):
    win = tk.Toplevel(root)
    win.title("Trackpad test")
    win.geometry("800x680")
    win.minsize(760, 640)
    names = detect_input_devices()["mouse / touchpad"]
    pad_names = [name for name in names if "touchpad" in name.lower() or "trackpad" in name.lower()]
    warning = (
        "Linux reports: " + "; ".join(pad_names)
        if pad_names
        else "Linux does not list a device named touchpad/trackpad. Test the built-in "
        "surface directly; an external mouse can also trigger these events."
    )

    tk.Label(
        win,
        text=warning,
        font=("sans", 10, "bold"),
        fg="#7a4b00",
        bg="#fff3cd",
        justify="left",
        wraplength=760,
        padx=8,
        pady=6,
    ).pack(fill="x", padx=10, pady=(10, 4))
    tk.Label(
        win,
        text="Use the built-in trackpad: tap/click, double-tap, move, drag, and two-finger scroll.",
        font=("sans", 11),
        anchor="w",
        wraplength=760,
    ).pack(fill="x", padx=10, pady=(0, 8))

    body = tk.Frame(win)
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    canvas = tk.Canvas(body, width=440, height=440, highlightthickness=0, bg="#f4f6f7")
    canvas.pack(side="left", fill="none", expand=False)
    canvas.create_rectangle(
        48, 48, 392, 392,
        fill="#dce4e8",
        outline="#455a64",
        width=3,
    )
    canvas.create_rectangle(
        108, 108, 332, 332,
        fill="#f8fbfb",
        outline="#607d8b",
        width=3,
    )
    canvas.create_text(
        220, 350, text="ONE CONTINUOUS TOUCH SURFACE", font=("sans", 9, "bold"),
        fill="#455a64",
    )
    pointer = canvas.create_oval(212, 212, 228, 228, fill="#1976d2", outline="")

    panel = tk.Frame(body, padx=18)
    panel.pack(side="left", fill="both", expand=True)
    tests = [
        ("tap", "Tap / primary click"),
        ("double", "Double tap"),
        ("secondary", "Secondary click"),
        ("move", "Pointer movement"),
        ("drag", "Press and drag"),
        ("scroll", "Two-finger scroll"),
    ]
    labels = {}
    for key, text in tests:
        label = tk.Label(panel, text="\u2610  " + text, font=("sans", 11), anchor="w")
        label.pack(fill="x", pady=3)
        labels[key] = label

    completed = set()
    motion_count = [0]
    press_position = [None]

    def mark(key):
        if key not in completed:
            completed.add(key)
            labels[key].config(text="\u2714  " + dict(tests)[key], fg=COLORS["pass"])

    def press(event):
        press_position[0] = (event.x, event.y)
        if event.num == 1:
            mark("tap")
        elif event.num == 3:
            mark("secondary")
        return "break"

    def motion(event):
        canvas.coords(pointer, event.x - 8, event.y - 8, event.x + 8, event.y + 8)
        motion_count[0] += 1
        if motion_count[0] >= 5:
            mark("move")
        if press_position[0] is not None:
            start_x, start_y = press_position[0]
            if abs(event.x - start_x) + abs(event.y - start_y) > 18:
                mark("drag")

    def release(_event):
        press_position[0] = None

    def scroll(event, direction=None):
        if direction is not None or event.delta:
            mark("scroll")
        return "break"

    def reset():
        completed.clear()
        motion_count[0] = 0
        for key, text in tests:
            labels[key].config(text="\u2610  " + text, fg="black")

    canvas.bind("<ButtonPress>", press)
    canvas.bind("<ButtonRelease>", release)
    canvas.bind("<Double-Button-1>", lambda _event: mark("double"))
    canvas.bind("<Motion>", motion)
    canvas.bind("<MouseWheel>", scroll)
    canvas.bind("<Button-4>", lambda event: scroll(event, "up"))
    canvas.bind("<Button-5>", lambda event: scroll(event, "down"))
    tk.Button(panel, text="Reset", command=reset).pack(anchor="w", pady=12)
    tk.Label(
        panel,
        text="Tk receives pointer events from the desktop and cannot prove whether they came from the trackpad or a mouse.",
        justify="left",
        wraplength=360,
        fg="#555555",
    ).pack(anchor="w", pady=(8, 0))
    win.focus_force()