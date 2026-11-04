"""Battery health check. Returns (status, text); no GUI code."""

import glob
import os

from utils import read

POWER_SUPPLY_DIR = "/sys/class/power_supply"

# Health grades: each band is a quarter of 100%.
BATTERY_GRADES = [(80, "EXCELLENT"), (60, "GOOD"), (50, "FAIR"), (0, "POOR")]


def battery_grade(pct):
    for floor, name in BATTERY_GRADES:
        if pct >= floor:
            return name
    return "POOR"


def _num(value):
    """int(value), or None if it is missing or not a number."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _capacity(b):
    """(label, full, design, scale) from a MATCHING pair of sysfs files, else None.

    energy_* is microwatt-hours, charge_* is microamp-hours. Never mix the two.
    """
    for label, scale, full_f, design_f in (
        ("Wh", 1_000_000, "energy_full", "energy_full_design"),
        ("mAh", 1_000, "charge_full", "charge_full_design"),
    ):
        full, design = _num(read(f"{b}/{full_f}")), _num(read(f"{b}/{design_f}"))
        if full is not None and design:
            return label, full, design, scale
    return None


def _friendly(name, value):
    """Human-readable version of a raw sysfs value, or '' if there is none."""
    n = _num(value)
    if n is None:
        return ""
    if name.startswith("energy_"):
        return f"{n / 1e6:.2f} Wh"
    if name.startswith("charge_"):
        return f"{n / 1e3:.0f} mAh"
    if name.startswith("voltage_"):
        return f"{n / 1e6:.3f} V"
    if name.startswith("current_"):
        return f"{n / 1e3:.0f} mA"
    if name.startswith("power_"):
        return f"{n / 1e6:.2f} W"
    if name.startswith("temp"):
        return f"{n / 10:.1f} C"
    if name == "capacity":
        return f"{n}%"
    return ""


def _raw_attributes(b):
    rows = []
    for path in sorted(glob.glob(f"{b}/*")):
        name = os.path.basename(path)
        if name == "uevent" or not os.path.isfile(path):
            continue
        value = read(path)
        if value is None:
            continue
        extra = _friendly(name, value)
        rows.append(f"  {name}: {value}" + (f"   (= {extra})" if extra else ""))
    return rows


def check_battery():
    bats = sorted(glob.glob(f"{POWER_SUPPLY_DIR}/BAT*"))
    if not bats:
        return "info", "No battery detected (desktop, or battery not reported)."
    lines, worst = [], "pass"
    for b in bats:
        name = os.path.basename(b)
        status = read(f"{b}/status") or "unknown"
        cycles = read(f"{b}/cycle_count")
        if cycles is None:
            cycles = "n/a"
        elif _num(cycles) == 0:
            cycles = "0 (may not be tracked by this battery)"
        lines.append(f"{name}: {status}, cycles: {cycles}")

        cap = _capacity(b)
        if cap:
            unit, full, design, scale = cap
            pct = full * 1000 // design / 10  # truncated to 0.1% so display and grade agree
            grade = battery_grade(pct)
            lines.append(f"  Health: {pct:.1f}%  ({grade})")
            if unit == "Wh":
                lines.append(f"  Full charge: {full / scale:.2f} Wh   Design: {design / scale:.2f} Wh")
            else:
                lines.append(f"  Full charge: {full / scale:.0f} mAh   Design: {design / scale:.0f} mAh")
            if grade == "POOR":
                worst = "fail"
            elif grade == "FAIR" and worst == "pass":
                worst = "warn"
        else:
            lines.append("  Health: not reported by this battery")
            worst = "warn" if worst == "pass" else worst
        charge = read(f"{b}/capacity")
        if charge:
            lines.append(f"  Current charge: {charge}%")

    others = [p for p in sorted(glob.glob(f"{POWER_SUPPLY_DIR}/*")) if p not in bats]
    if others:
        lines.append("\nOther power sources:")
        for p in others:
            lines.append(
                f"  {os.path.basename(p)}: type={read(f'{p}/type') or '?'}, online={read(f'{p}/online') or '?'}"
            )

    for b in bats:
        lines.append(f"\nRaw data - {os.path.basename(b)} ({b}):")
        lines.extend(_raw_attributes(b) or ["  (nothing readable)"])
    return worst, "\n".join(lines)
