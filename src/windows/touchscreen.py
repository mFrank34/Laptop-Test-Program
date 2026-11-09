"""Touchscreen tap-target and swipe tester using desktop pointer events."""

import tkinter as tk

from theme import COLORS, KEY_DONE, KEY_HELD


def touchscreen_window(root):
    win = tk.Toplevel(root)
    win.title("Touchscreen test")
    win.geometry("860x800")
    win.minsize(820, 760)
    header = tk.Frame(win, bg="#176b68", padx=16, pady=12)
    header.pack(fill="x")
    tk.Label(
        header,
        text="Touchscreen test",
        font=("sans", 16, "bold"),
        fg="white",
        bg="#176b68",
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Tap each square, then swipe across the test area.",
        font=("sans", 10),
        fg="#e5f3f1",
        bg="#176b68",
    ).pack(anchor="w", pady=(2, 0))
    tk.Label(
        win,
        text="This checks touch-generated pointer input. The desktop reports touch and mouse through the same Tk events, so use your finger and avoid the mouse for this test.",
        justify="left",
        wraplength=820,
        fg="#555555",
    ).pack(anchor="w", padx=16, pady=10)

    body = tk.Frame(win, bg="#f4f6f6")
    body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
    canvas = tk.Canvas(body, width=600, height=600, bg="#eaf0ef", highlightthickness=0)
    canvas.pack(side="left", fill="none", expand=False)
    panel = tk.Frame(body, padx=18, bg="#f4f6f6")
    panel.pack(side="left", fill="both", expand=True)
    tk.Label(
        panel,
        text="TARGETS",
        font=("sans", 10, "bold"),
        fg="#425957",
        bg="#f4f6f6",
    ).pack(anchor="w", pady=(6, 8))

    positions = [
        (100, 100), (300, 100), (500, 100),
        (100, 300), (300, 300), (500, 300),
        (100, 500), (300, 500), (500, 500),
    ]
    targets = {}
    for index, (x, y) in enumerate(positions, 1):
        tile = canvas.create_rectangle(
            x - 46, y - 46, x + 46, y + 46,
            fill="#ffffff", outline="#78928f", width=2,
        )
        text = canvas.create_text(
            x, y, text=str(index), font=("sans", 18, "bold"), fill="#263a38"
        )
        targets[index] = (tile, text, (x, y))

    status = {
        index: tk.Label(
            panel, text=f"\u2610  Target {index}", font=("sans", 10), anchor="w", bg="#f4f6f6"
        )
        for index in targets
    }
    for label in status.values():
        label.pack(fill="x", pady=3)
    progress = tk.Label(panel, text="0 of 9 targets", font=("sans", 10, "bold"), fg="#176b68", bg="#f4f6f6")
    progress.pack(anchor="w", pady=(12, 4))
    swipe_status = tk.Label(
        panel, text="\u2610  Swipe", font=("sans", 10), anchor="w", bg="#f4f6f6"
    )
    swipe_status.pack(fill="x", pady=4)
    info = tk.Label(
        panel, text="Touch the squares with your finger.", justify="left", wraplength=180,
        bg="#f4f6f6", fg="#52615f",
    )
    info.pack(anchor="w", pady=(10, 0))

    tapped = set()
    gesture = {"start": None, "target": None, "distance": 0}

    def mark_target(index):
        if index in tapped:
            canvas.itemconfig(targets[index][0], fill=KEY_DONE)
            return
        tapped.add(index)
        circle, _text, _position = targets[index]
        canvas.itemconfig(circle, fill=KEY_DONE)
        status[index].config(text=f"\u2714  Target {index}", fg=COLORS["pass"])
        progress.config(text=f"{len(tapped)} of 9 targets")
        if len(tapped) == len(targets):
            info.config(text="All touch targets responded.")

    def press(event):
        gesture.update(start=(event.x, event.y), target=None, distance=0)
        closest = min(
            targets,
            key=lambda index: (targets[index][2][0] - event.x) ** 2
            + (targets[index][2][1] - event.y) ** 2,
        )
        x, y = targets[closest][2]
        if abs(x - event.x) <= 56 and abs(y - event.y) <= 56:
            gesture["target"] = closest
            canvas.itemconfig(targets[closest][0], fill=KEY_HELD)
        return "break"

    def motion(event):
        if gesture["start"] is None:
            return
        start_x, start_y = gesture["start"]
        gesture["distance"] = max(
            gesture["distance"], abs(event.x - start_x) + abs(event.y - start_y)
        )

    def release(_event):
        target = gesture["target"]
        if target is not None and gesture["distance"] < 30:
            mark_target(target)
        elif target is not None and target not in tapped:
            canvas.itemconfig(targets[target][0], fill="#ffffff")
        if gesture["distance"] >= 100:
            swipe_status.config(text="\u2714  Swipe", fg=COLORS["pass"])
            info.config(text="Swipe gesture detected.")
        elif target is None:
            info.config(text="Touch a numbered target or swipe across the area.")
        gesture.update(start=None, target=None, distance=0)
        return "break"

    def reset():
        tapped.clear()
        for index, (circle, _text, _position) in targets.items():
            canvas.itemconfig(circle, fill="#ffffff")
            status[index].config(text=f"\u2610  Target {index}", fg="black")
        progress.config(text="0 of 9 targets")
        swipe_status.config(text="\u2610  Swipe", fg="black")
        info.config(text="Touch targets with your finger.")

    canvas.bind("<ButtonPress-1>", press)
    canvas.bind("<B1-Motion>", motion)
    canvas.bind("<ButtonRelease-1>", release)
    tk.Button(panel, text="Reset", command=reset).pack(anchor="w", pady=16)
    win.focus_force()