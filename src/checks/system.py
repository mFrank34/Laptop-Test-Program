"""System summary, USB listing and shutdown. Each returns (status, text)."""

import os
import math
import shutil
import struct
import subprocess
import tempfile
import wave

from utils import read, run


def check_usb():
    code, out = run(["lsusb"])
    if code != 0:
        return "warn", out
    return "info", out


def added_usb_devices(previous, current):
    return sorted(set(current.splitlines()) - set(previous.splitlines()))


def play_usb_chime():
    """Play a short two-note chime. Returns (True, "") or (False, reason it failed)."""
    players = []
    for name, options in (("aplay", ["-q"]), ("paplay", [])):
        player = shutil.which(name)
        if player:
            players.append([player, *options])
    if not players:
        return False, "No audio player is installed (aplay / paplay)."

    cards = read("/proc/asound/cards") or ""
    if not cards.strip() or "no soundcards" in cards.lower():
        return False, "No sound card was detected."

    sample_rate = 22050
    frames = bytearray()
    for frequency, duration in ((880, 0.12), (1175, 0.18)):
        frame_count = int(sample_rate * duration)
        for frame in range(frame_count):
            envelope = min(frame / 180, (frame_count - frame) / 180, 1)
            sample = int(
                9000
                * envelope
                * math.sin(2 * math.pi * frequency * frame / sample_rate)
            )
            frames.extend(struct.pack("<h", sample))

    last_error = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio_file:
            with wave.open(audio_file, "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(sample_rate)
                audio.writeframes(frames)
            for command in players:
                try:
                    result = subprocess.run(
                        [*command, audio_file.name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                except (OSError, subprocess.SubprocessError) as e:
                    last_error = str(e)
                    continue
                if result.returncode == 0:
                    return True, ""
                last_error = (result.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        last_error = str(e)
    return False, last_error or "Audio playback failed."


def check_summary():
    cpu = "unknown"
    for line in (read("/proc/cpuinfo") or "").splitlines():
        if line.startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
    mem = "unknown"
    for line in (read("/proc/meminfo") or "").splitlines():
        if line.startswith("MemTotal"):
            mem = f"{int(line.split()[1]) / 1024 / 1024:.1f} GB"
            break
    vendor = read("/sys/class/dmi/id/sys_vendor") or "?"
    product = read("/sys/class/dmi/id/product_name") or "?"
    serial = read("/sys/class/dmi/id/product_serial") or "n/a (needs root)"
    return (
        "info",
        f"System: {vendor} {product}\nSerial: {serial}\nCPU: {cpu}\nRAM: {mem}",
    )


def shutdown_system():
    """Power off. Returns (status, text) instead of opening a dialog, so the GUI decides how to show it."""
    cmd = ["poweroff"] if os.geteuid() == 0 else ["sudo", "-n", "poweroff"]
    code, out = run(cmd, timeout=10)
    if code != 0:
        return "fail", f"Shutdown failed:\n{out or 'Unknown error'}"
    return "pass", "Shutdown command sent."
