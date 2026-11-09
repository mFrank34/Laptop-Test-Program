"""Automatic input, audio, and kernel-driver diagnostics for Linux."""

import glob
import os


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            return file.read().strip()
    except OSError:
        return ""


def _input_devices(text):
    devices = {"keyboard": [], "mouse / touchpad": []}
    for block in text.split("\n\n"):
        name = ""
        handlers = ""
        for line in block.splitlines():
            if line.startswith("N: Name="):
                name = line.partition('"')[2].partition('"')[0]
            elif line.startswith("H: Handlers="):
                handlers = line.partition("=")[2].split()
        if not name:
            continue
        if "kbd" in handlers:
            devices["keyboard"].append(name)
        if any(handler.startswith("mouse") for handler in handlers) or any(
            word in name.lower() for word in ("mouse", "touchpad", "trackpad")
        ):
            devices["mouse / touchpad"].append(name)
    return devices


def detect_input_devices(proc_root="/proc"):
    """Return Linux-registered keyboard and mouse/touchpad names."""
    return _input_devices(_read(os.path.join(proc_root, "bus", "input", "devices")))


def _bus_devices(sys_root):
    devices = []
    for bus in ("pci", "usb"):
        for path in sorted(glob.glob(os.path.join(sys_root, "bus", bus, "devices", "*"))):
            if not os.path.isdir(path):
                continue
            name = _read(os.path.join(path, "product"))
            if not name and bus == "pci":
                vendor = _read(os.path.join(path, "vendor"))
                device = _read(os.path.join(path, "device"))
                name = " ".join(part for part in (vendor, device) if part)
            if not name:
                name = os.path.basename(path)
            driver_path = os.path.join(path, "driver")
            driver = os.path.basename(os.path.realpath(driver_path)) if os.path.islink(driver_path) else ""
            devices.append((bus, name, driver))
    return devices


def check_devices(proc_root="/proc", sys_root="/sys"):
    """Report detected input/audio hardware and PCI/USB devices without drivers."""
    inputs = detect_input_devices(proc_root)
    audio_cards = _read(os.path.join(proc_root, "asound", "cards"))
    has_audio = bool(audio_cards and "no soundcards" not in audio_cards.lower())
    if not has_audio:
        has_audio = bool(glob.glob(os.path.join(sys_root, "class", "sound", "card[0-9]*")))

    lines = []
    missing = []
    for kind in ("keyboard", "mouse / touchpad"):
        names = inputs[kind]
        if names:
            lines.append(
                f"{kind.title()}: detected ({'; '.join(names)}) "
                "[needs functional testing]"
            )
        else:
            lines.append(f"{kind.title()}: NOT DETECTED [needs further inspection]")
            missing.append(kind)
    if has_audio:
        lines.append("Audio: detected (ALSA sound card present) [needs speaker testing]")
    else:
        lines.append("Audio: NOT DETECTED [needs further inspection]")
        missing.append("audio")

    devices = _bus_devices(sys_root)
    unbound = [(bus, name) for bus, name, driver in devices if not driver]
    lines.append(f"PCI/USB devices: {len(devices)} detected")
    if unbound:
        lines.append(f"Devices without a bound driver: {len(unbound)} [needs driver investigation]")
        lines.extend(
            f"  {bus.upper()}: {name} [needs driver investigation]"
            for bus, name in unbound[:20]
        )
        if len(unbound) > 20:
            lines.append(f"  ... and {len(unbound) - 20} more")
    elif devices:
        lines.append("Driver binding: all listed PCI/USB devices have a driver")
    else:
        lines.append("Driver binding: PCI/USB inventory unavailable")

    if missing:
        lines.append("\nMissing expected devices: " + ", ".join(missing))
    if unbound:
        lines.append("\nUnbound devices may be unsupported, disabled, or intentionally driverless.")
    lines.append("\nDetection does not confirm that a device works; perform the functional tests.")

    status = "warn" if missing or unbound or not devices else "info"
    return status, "\n".join(lines)