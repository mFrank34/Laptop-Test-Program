"""Mouse / touchpad tester window."""

import tkinter as tk

from checks.devices import detect_input_devices
from theme import COLORS, KEY_DONE, KEY_HELD, KEY_IDLE


def mouse_window(root):
    win = tk.Toplevel(root)
    win.title("Mouse / touchpad test")
    win.geometry("700x440")
    mouse_names = detect_input_devices()["mouse / touchpad"]
    canvas = tk.Canvas(win, width=320, height=420, highlightthickness=0)
    canvas.pack(side="left", padx=10, pady=10)
    panel = tk.Frame(win)
    panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    warning = (
        "Linux does not currently detect a mouse or touchpad. Check its connection, "
        "Fn/firmware disable settings, or try an external mouse."
        if not mouse_names
        else "If the pointer or buttons do not respond, check for a touchpad/Fn "
        "disable toggle or firmware setting. Detection does not verify operation."
    )
    tk.Label(
        panel, text=warning, font=("sans", 10, "bold"), fg="#7a4b00", bg="#fff3cd",
        justify="left", wraplength=340, padx=8, pady=6,
    ).pack(fill="x", pady=(0, 8))
    tk.Label(
        panel, text="Try each action. Ticks turn green.", font=("sans", 12, "bold")
    ).pack(anchor="w", pady=(0, 8))

    canvas.create_polygon(
        100, 30, 200, 30, 230, 60, 230, 320, 200, 350, 100, 350, 70, 320, 70, 60,
        smooth=True, fill="#cfd8dc", outline="#455a64", width=3,
    )
    parts = {
        "left": canvas.create_rectangle(84, 44, 147, 170, fill=KEY_IDLE, outline="#455a64", width=2),
        "right": canvas.create_rectangle(153, 44, 216, 170, fill=KEY_IDLE, outline="#455a64", width=2),
        "middle": canvas.create_rectangle(141, 70, 159, 130, fill=KEY_IDLE, outline="#455a64", width=2),
        "back": canvas.create_rectangle(56, 120, 70, 160, fill=KEY_IDLE, outline="#455a64", width=2),
        "fwd": canvas.create_rectangle(56, 170, 70, 210, fill=KEY_IDLE, outline="#455a64", width=2),
    }
    up = canvas.create_text(270, 90, text="\u25b2", font=("sans", 26), fill="#90a4ae")
    down = canvas.create_text(270, 140, text="\u25bc", font=("sans", 26), fill="#90a4ae")
    pos = canvas.create_text(150, 385, text="", font=("monospace", 11))

    tests = [
        ("left", "Left click"),
        ("right", "Right click"),
        ("middle", "Middle click (press the wheel)"),
        ("up", "Scroll up"),
        ("down", "Scroll down"),
        ("double", "Double click"),
        ("move", "Move the pointer around"),
        ("drag", "Hold left button and drag"),
        ("back", "Side button back (if fitted)"),
        ("fwd", "Side button forward (if fitted)"),
    ]
    names = dict(tests)
    labels = {}
    for key, name in tests:
        labels[key] = tk.Label(
            panel, text="\u2610  " + name, font=("sans", 12), anchor="w"
        )
        labels[key].pack(fill="x", pady=1)
    done, motion = set(), [0]

    def mark(key):
        if key not in done:
            done.add(key)
            labels[key].config(text="\u2714  " + names[key], fg=COLORS["pass"])

    def flash(item):
        canvas.itemconfig(item, fill=KEY_HELD)
        win.after(200, lambda: canvas.itemconfig(item, fill=COLORS["pass"]))

    buttons = {1: "left", 2: "middle", 3: "right", 8: "back", 9: "fwd"}

    def press(e):
        if e.num in buttons:
            key = buttons[e.num]
            canvas.itemconfig(parts[key], fill=KEY_HELD)
            mark(key)
        elif e.num == 4:
            mark("up")
            flash(up)
        elif e.num == 5:
            mark("down")
            flash(down)

    def release(e):
        if e.num in buttons:
            canvas.itemconfig(parts[buttons[e.num]], fill=KEY_DONE)

    def wheel(e):
        if e.delta > 0:
            mark("up")
            flash(up)
        elif e.delta < 0:
            mark("down")
            flash(down)

    def motion_ev(e):
        motion[0] += 1
        canvas.itemconfig(pos, text=f"x={e.x_root}  y={e.y_root}")
        if motion[0] > 40:
            mark("move")
        if e.state & 0x100 and motion[0] > 10:  # left button held
            mark("drag")

    def reset():
        done.clear()
        motion[0] = 0
        for key, name in names.items():
            labels[key].config(text="\u2610  " + name, fg="black")
        for item in parts.values():
            canvas.itemconfig(item, fill=KEY_IDLE)

    win.bind("<ButtonPress>", press)
    win.bind("<ButtonRelease>", release)
    win.bind("<MouseWheel>", wheel)
    win.bind("<Double-Button-1>", lambda e: mark("double"))
    win.bind("<Motion>", motion_ev)
    tk.Button(panel, text="Reset", command=reset).pack(anchor="w", pady=10)
    win.focus_force()
