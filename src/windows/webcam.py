"""Live webcam preview. ffmpeg reads the camera and hands us plain RGB frames."""

import glob
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import tkinter as tk

from theme import COLORS
from utils import read
from windows.window_size import fit_window

CAM_W, CAM_H = 640, 360


def find_cameras():
    """Return [(device_path, friendly_name)] for camera capture nodes."""
    cams = []
    for path in sorted(
        glob.glob("/dev/video*"),
        key=lambda p: int(p[10:] or 0) if p[10:].isdigit() else 0,
    ):
        node = os.path.basename(path)
        if (read(f"/sys/class/video4linux/{node}/index") or "0") != "0":
            continue  # skip metadata / secondary nodes
        cams.append((path, read(f"/sys/class/video4linux/{node}/name") or node))
    return cams


def build_ffmpeg_cmd(device):
    """ffmpeg reads the camera in any format and gives us plain RGB frames of a fixed size."""
    fit = (
        f"fps=15,scale={CAM_W}:{CAM_H}:force_original_aspect_ratio=decrease,"
        f"pad={CAM_W}:{CAM_H}:(ow-iw)/2:(oh-ih)/2"
    )
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-fflags", "nobuffer", "-flags", "low_delay",
        "-f", "v4l2", "-i", device,
        "-vf", fit,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]


def _frame_reader(proc, frames, stop):
    size = CAM_W * CAM_H * 3
    while not stop.is_set():
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        try:
            frames.put_nowait(buf)
        except queue.Full:
            try:
                frames.get_nowait()  # drop the old frame, keep the newest
            except queue.Empty:
                pass
            frames.put_nowait(buf)
    frames.put(None)  # tell the window the stream ended


def webcam_window(root):
    win = tk.Toplevel(root)
    win.title("Webcam test")
    wraplength = max(240, win.winfo_screenwidth() - 60)
    if not shutil.which("ffmpeg"):
        tk.Label(
            win, padx=30, pady=30, justify="left", font=("sans", 12),
            wraplength=wraplength,
            text="The webcam preview needs ffmpeg.\n\nInstall it with:\n    sudo apt install ffmpeg",
        ).pack()
        fit_window(win, 480, 240, min_width=320, min_height=180)
        return
    cams = find_cameras()
    if not cams:
        tk.Label(
            win, padx=30, pady=30, font=("sans", 12),
            wraplength=wraplength,
            text="No camera detected (no /dev/video device).",
        ).pack()
        fit_window(win, 480, 240, min_width=320, min_height=180)
        return

    choice = tk.StringVar(value=f"{cams[0][1]}  ({cams[0][0]})")
    top = tk.Frame(win)
    top.pack(fill="x", padx=10, pady=8)
    camera_menu = tk.OptionMenu(top, choice, *[f"{n}  ({p})" for p, n in cams])
    camera_menu.configure(wraplength=wraplength, justify="left")
    camera_menu.pack(side="left")
    go_btn = tk.Button(top, text="Start", width=8)
    go_btn.pack(side="left", padx=8)
    status = tk.Label(win, text="Press Start.", font=("sans", 11), wraplength=wraplength)
    status.pack()
    blank = tk.PhotoImage(width=CAM_W, height=CAM_H)
    screen = tk.Label(win, image=blank, bg="black")
    screen.pack(padx=10, pady=8)
    screen.image = blank

    state = {"proc": None, "stop": None, "frames": None, "err": None, "count": 0, "t0": 0.0, "closed": False}

    def stop_stream():
        if state["stop"]:
            state["stop"].set()
        proc = state["proc"]
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        state["proc"] = None
        state["frames"] = None  # discard any leftover frames
        go_btn.config(text="Start")

    def start_stream():
        device = choice.get().rsplit("(", 1)[1].rstrip(")")
        stop_stream()
        state["err"] = tempfile.TemporaryFile()
        try:
            proc = subprocess.Popen(
                build_ffmpeg_cmd(device), stdout=subprocess.PIPE, stderr=state["err"]
            )
        except OSError as err:
            status.config(text=f"Could not start ffmpeg: {err}", fg=COLORS["fail"])
            return
        state.update(
            proc=proc,
            stop=threading.Event(),
            frames=queue.Queue(maxsize=2),
            count=0,
            t0=time.time(),
        )
        threading.Thread(
            target=_frame_reader,
            args=(proc, state["frames"], state["stop"]),
            daemon=True,
        ).start()
        status.config(text="Starting camera...", fg="black")
        go_btn.config(text="Stop")

    def toggle():
        if state["proc"]:
            stop_stream()
            status.config(text="Stopped.", fg="black")
        else:
            start_stream()

    def poll():
        if state["closed"]:
            return  # window is gone, stop polling
        frames = state["frames"]
        latest, ended = None, False
        if frames:
            try:
                while True:
                    item = frames.get_nowait()
                    if item is None:
                        ended = True
                    else:
                        latest = item
            except queue.Empty:
                pass
        if latest:
            photo = tk.PhotoImage(data=b"P6\n%d %d\n255\n" % (CAM_W, CAM_H) + latest)
            screen.config(image=photo)
            screen.image = photo
            state["count"] += 1
            secs = max(time.time() - state["t0"], 0.1)
            status.config(
                text=f"Camera working - {CAM_W}x{CAM_H}, about {state['count'] / secs:.0f} fps",
                fg=COLORS["pass"],
            )
        if ended and state["proc"]:
            state["err"].seek(0)
            lines = state["err"].read().decode(errors="replace").strip().splitlines()
            stop_stream()
            status.config(
                text=("Camera stopped: " + lines[-1]) if lines else "Camera stopped.",
                fg=COLORS["fail"],
            )
        win.after(40, poll)

    def close():
        state["closed"] = True
        stop_stream()
        win.destroy()

    go_btn.config(command=toggle)
    win.protocol("WM_DELETE_WINDOW", close)
    win.after(40, poll)
    fit_window(win, CAM_W + 80, CAM_H + 140, min_width=360, min_height=300)
