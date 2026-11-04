"""Full-screen colour cycle to spot dead pixels and backlight problems."""

import tkinter as tk


def screen_window(root):
    win = tk.Toplevel(root)
    win.attributes("-fullscreen", True)
    colors = ["black", "white", "red", "green", "blue"]
    idx = [0]
    win.config(bg=colors[0], cursor="none")
    label = tk.Label(
        win,
        text="Click or press a key for the next colour.  Esc to exit.",
        bg="gray20",
        fg="white",
    )
    label.place(x=10, y=10)

    def nxt(_e=None):
        idx[0] += 1
        if idx[0] >= len(colors):
            win.destroy()
            return
        win.config(bg=colors[idx[0]])
        label.destroy()

    win.bind("<Button-1>", nxt)
    win.bind("<space>", nxt)
    win.bind("<Return>", nxt)
    win.bind("<Escape>", lambda e: win.destroy())
    win.focus_force()
