"""System summary, USB listing and shutdown. Each returns (status, text)."""

import os

from utils import read, run


def check_usb():
    code, out = run(["lsusb"])
    if code != 0:
        return "warn", out
    return "info", out


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
