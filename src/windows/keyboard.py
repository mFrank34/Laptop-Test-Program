"""Keyboard tester window: every key lights up while held and turns green once tested."""

import os
import queue
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

from checks.devices import detect_input_devices
from theme import KEY_DONE, KEY_HELD, KEY_IDLE
from windows.keyboard_layout import RAW_NAMES, keyboard_layout
from windows.raw_input import raw_key_listener


def keyboard_window(root):
    unit = 44
    win = tk.Toplevel(root)
    win.title("Keyboard test")
    win.geometry(f"{int(18.5 * unit) + 30}x{int(6.5 * unit) + 400}")
    keyboard_names = detect_input_devices()["keyboard"]
    warning = (
        "Linux does not currently detect a keyboard. Check any Fn/keyboard-disable "
        "toggle or firmware settings."
        if not keyboard_names
        else "If keys do not respond, check for a keyboard-disable/Fn toggle or "
        "firmware setting. This screen cannot read that setting directly."
    )
    tk.Label(
        win, text=warning, font=("sans", 10, "bold"), fg="#7a4b00", bg="#fff3cd",
        wraplength=800, justify="left", padx=8, pady=6,
    ).pack(fill="x", padx=8, pady=(8, 2))
    tk.Label(
        win,
        text="Press every key. Keys light up while held and turn green once tested.",
        font=("sans", 12),
    ).pack(pady=(4, 2))
    counter = tk.Label(win, font=("sans", 16, "bold"), fg="#1565c0")
    counter.pack()
    canvas = tk.Canvas(
        win,
        width=int(18.5 * unit) + 4,
        height=int(6.5 * unit) + 4,
        highlightthickness=0,
    )
    canvas.pack(pady=6)

    shapes, names = {}, {}
    for label, code, x, y, w, h in keyboard_layout():
        x0, y0 = x * unit + 2, y * unit + 2
        rect = canvas.create_rectangle(
            x0, y0, x0 + w * unit - 3, y0 + h * unit - 3,
            fill=KEY_IDLE, outline="#90a4ae", width=2,
        )
        text = canvas.create_text(
            x0 + (w * unit - 3) / 2,
            y0 + (h * unit - 3) / 2,
            text=label,
            font=("sans", 9),
        )
        shapes[code] = (rect, text)
        names[code] = label or "Space"

    bar = tk.Frame(win)
    bar.pack(fill="x", padx=10)
    tk.Label(bar, text="Key listener", font=("sans", 11, "bold")).pack(side="left")
    log = scrolledtext.ScrolledText(
        win, height=8, font=("monospace", 10), state="disabled"
    )
    log.pack(fill="both", expand=True, padx=10, pady=(2, 6))
    log.tag_config("missing", foreground="#c62828")
    log.tag_config("info", foreground="#555555")

    def logline(text, tag=""):
        log.config(state="normal")
        log.insert("end", text + "\n", tag)
        log.see("end")
        log.config(state="disabled")

    tested, others, last_seen = set(), set(), {}
    stop, raw_q, raw_thread = threading.Event(), queue.Queue(), [None]

    def refresh():
        counter.config(text=f"{len(tested)} of {len(shapes)} keys tested")

    def paint(code, colour):
        canvas.itemconfig(shapes[code][0], fill=colour)

    def press(e):
        on_layout = e.keycode in shapes
        if on_layout:
            tested.add(e.keycode)
            paint(e.keycode, KEY_HELD)
        else:
            others.add(e.keycode)
        now = time.time()
        if now - last_seen.get(e.keycode, 0) > 0.6:  # hide auto-repeat spam
            where = (
                f"= '{names[e.keycode]}' on layout" if on_layout else "NOT ON LAYOUT"
            )
            logline(
                f"X keycode {e.keycode:>3}    keysym {e.keysym:<16} {where}",
                "" if on_layout else "missing",
            )
        last_seen[e.keycode] = now
        refresh()
        return "break"

    def release(e):
        if e.keycode in shapes:
            paint(e.keycode, KEY_DONE)
        last_seen[e.keycode] = time.time()
        return "break"

    def poll_raw():
        try:
            while True:
                item = raw_q.get_nowait()
                if item[0] == "info":
                    logline(item[1], "info")
                else:
                    _, code, dev = item
                    x_code = code + 8
                    name = RAW_NAMES.get(code) or (
                        names.get(x_code) if x_code in shapes else "unknown"
                    )
                    on = x_code in shapes
                    logline(
                        f"RAW  code {code:>3} (X {x_code:>3})  {name:<20} from {dev}",
                        "" if on else "missing",
                    )
        except queue.Empty:
            pass
        if not stop.is_set():
            win.after(100, poll_raw)

    def toggle_raw():
        if raw_var.get():
            if os.geteuid() != 0:
                raw_var.set(False)
                logline("Raw listener needs root. Start the tool with sudo.", "info")
                return
            stop.clear()
            raw_thread[0] = threading.Thread(
                target=raw_key_listener, args=(raw_q, stop), daemon=True
            )
            raw_thread[0].start()
        else:
            stop.set()
            logline("Raw listener stopped.", "info")
            stop.clear()

    def copy_log():
        win.clipboard_clear()
        win.clipboard_append(log.get("1.0", "end"))

    def clear_all():
        tested.clear()
        others.clear()
        for code in shapes:
            paint(code, KEY_IDLE)
        log.config(state="normal")
        log.delete("1.0", "end")
        log.config(state="disabled")
        refresh()

    def close():
        stop.set()
        win.destroy()

    raw_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        bar,
        text="Raw hardware listener (needs sudo, catches Fn / media keys)",
        variable=raw_var,
        command=toggle_raw,
    ).pack(side="left", padx=12)
    tk.Button(bar, text="Copy log", command=copy_log).pack(side="right")
    tk.Button(bar, text="Reset", command=clear_all).pack(side="right", padx=6)

    logline(
        "Press any key. Keys not on the layout above are shown in red with their keycode.",
        "info",
    )
    win.bind("<KeyPress>", press)
    win.bind("<KeyRelease>", release)
    win.protocol("WM_DELETE_WINDOW", close)
    win.after(100, poll_raw)
    refresh()
    win.focus_force()
