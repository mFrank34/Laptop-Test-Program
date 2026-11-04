"""Storage drive check: make/model, serial, size, type, partitions and (optional) SMART health.

Returns (status, text) like the other checks. No GUI code.
Uses lsblk (util-linux) and falls back to /sys/block if lsblk is missing.
SMART data needs smartmontools AND root; without them everything else still works.
"""

import glob
import json
import os
import shutil

from utils import read, run

DISK_COLS = "NAME,TYPE,SIZE,MODEL,VENDOR,SERIAL,REV,TRAN,ROTA,RM,HOTPLUG,WWN,STATE"
PART_COLS = "NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINT"
SKIP_PREFIXES = ("loop", "ram", "zram", "dm-", "md", "sr", "fd", "nbd")

# SMART attribute ids that matter on SATA drives
ATTR_REALLOCATED, ATTR_PENDING, ATTR_UNCORRECTABLE = 5, 197, 198


# ---------------------------------------------------------------- helpers


def _num(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _flag(value):
    """lsblk gives booleans, '1'/'0' strings or null depending on the version."""
    return str(value).strip().lower() in ("1", "true")


def _size_text(n):
    if not n:
        return "unknown"
    return f"{n / 1e9:.1f} GB ({n / 2**30:.1f} GiB)"


def _short_size(n):
    if not n:
        return "?"
    if n >= 1e9:
        return f"{n / 1e9:.1f} GB"
    return f"{n / 1e6:.0f} MB"


def _lsblk(cols, *args):
    """Run lsblk and return parsed JSON, or None."""
    code, out = run(["lsblk", "-J", "-b", "-o", cols, *args])
    if code != 0:
        return None
    try:
        return json.loads(out[out.find("{"):])
    except ValueError:
        return None


# ---------------------------------------------------------------- finding disks


def _disks_from_lsblk():
    data = _lsblk(DISK_COLS, "-d")
    if not data:
        return None
    disks = []
    for d in data.get("blockdevices", []):
        name = d.get("name") or ""
        if d.get("type") != "disk" or name.startswith(SKIP_PREFIXES):
            continue
        disks.append(
            {
                "name": name,
                "size": _num(d.get("size")),
                "model": (d.get("model") or "").strip(),
                "vendor": (d.get("vendor") or "").strip(),
                "serial": (d.get("serial") or "").strip(),
                "rev": (d.get("rev") or "").strip(),
                "tran": (d.get("tran") or "").strip(),
                "rota": _flag(d.get("rota")),
                "removable": _flag(d.get("rm")) or _flag(d.get("hotplug")),
                "wwn": (d.get("wwn") or "").strip(),
                "state": (d.get("state") or "").strip(),
            }
        )
    return disks


def _disks_from_sysfs():
    """Fallback when lsblk is not installed."""
    disks = []
    for path in sorted(glob.glob("/sys/block/*")):
        name = os.path.basename(path)
        if name.startswith(SKIP_PREFIXES):
            continue
        sectors = _num(read(f"{path}/size")) or 0
        disks.append(
            {
                "name": name,
                "size": sectors * 512,
                "model": read(f"{path}/device/model") or "",
                "vendor": read(f"{path}/device/vendor") or "",
                "serial": read(f"{path}/device/serial") or "",
                "rev": read(f"{path}/device/firmware_rev") or read(f"{path}/device/rev") or "",
                "tran": "nvme" if name.startswith("nvme") else "",
                "rota": read(f"{path}/queue/rotational") == "1",
                "removable": read(f"{path}/removable") == "1",
                "wwn": read(f"{path}/device/wwid") or "",
                "state": read(f"{path}/device/state") or "",
            }
        )
    return disks


def _partitions(name):
    """Flat list of partitions/children under a disk, or []."""
    data = _lsblk(PART_COLS, f"/dev/{name}")
    if not data or not data.get("blockdevices"):
        return []
    rows = []

    def walk(nodes, depth):
        for n in nodes:
            rows.append((depth, n))
            walk(n.get("children", []), depth + 1)

    walk(data["blockdevices"][0].get("children", []), 0)
    return rows


# ---------------------------------------------------------------- SMART (optional)


def _smart(dev):
    """Returns (level, text). level is pass / warn / fail / None (no data)."""
    if not shutil.which("smartctl"):
        return None, "not checked (install: sudo apt install smartmontools)"
    if os.geteuid() != 0:
        return None, "not checked (run with sudo)"
    _code, out = run(["smartctl", "-a", "-j", dev], timeout=25)
    try:
        data = json.loads(out[out.find("{"):])
    except ValueError:
        return None, "could not read SMART data"

    status = data.get("smart_status")
    if status is None:
        return None, "not supported by this drive or USB adapter"

    level = "pass" if status.get("passed") else "fail"
    bits = ["PASSED" if status.get("passed") else "FAILED"]

    hours = (data.get("power_on_time") or {}).get("hours")
    if hours is not None:
        bits.append(f"power-on {hours} h (~{hours / 24:.0f} days)")
    temp = (data.get("temperature") or {}).get("current")
    if temp is not None:
        bits.append(f"temp {temp} C")

    nvme = data.get("nvme_smart_health_information_log")
    if nvme:
        used = nvme.get("percentage_used")
        if used is not None:
            bits.append(f"wear {used}% used")
            if used >= 90 and level == "pass":
                level = "warn"
        errors = nvme.get("media_errors")
        if errors:
            bits.append(f"media errors {errors}")
            if level == "pass":
                level = "warn"

    table = (data.get("ata_smart_attributes") or {}).get("table", [])
    attrs = {a.get("id"): (a.get("raw") or {}).get("value") for a in table}
    for attr_id, label in (
        (ATTR_REALLOCATED, "reallocated"),
        (ATTR_PENDING, "pending"),
        (ATTR_UNCORRECTABLE, "uncorrectable"),
    ):
        value = attrs.get(attr_id)
        if value is not None:
            bits.append(f"{label} {value}")
            if value > 0 and level == "pass":
                level = "warn"
    return level, ", ".join(bits)


# ---------------------------------------------------------------- the check


def _drive_type(d):
    if d["tran"] == "nvme":
        kind = "NVMe SSD"
    elif d["rota"]:
        kind = "HDD"
    else:
        kind = "SSD"
    extra = []
    if d["tran"] and d["tran"] != "nvme":
        extra.append(d["tran"].upper())
    if d["removable"]:
        extra.append("removable")
    return kind + (f" ({', '.join(extra)})" if extra else "")


def check_drives():
    disks = _disks_from_lsblk()
    if disks is None:
        disks = _disks_from_sysfs()
    disks = [d for d in disks if d["size"]]  # hide empty card-reader slots (0 bytes)
    if not disks:
        return "warn", "No drives detected."

    lines, levels = [f"{len(disks)} drive(s) detected\n"], []
    for d in disks:
        vendor = "" if d["vendor"].upper() == "ATA" else d["vendor"]
        title = " ".join(x for x in (vendor, d["model"]) if x) or "Unknown model"
        lines.append(f"{d['name']}: {title}")
        lines.append(f"  Make/vendor: {vendor or 'n/a'}")
        lines.append(f"  Model:       {d['model'] or 'n/a'}")
        lines.append(f"  Serial:      {d['serial'] or 'n/a'}")
        if d["rev"]:
            lines.append(f"  Firmware:    {d['rev']}")
        lines.append(f"  Size:        {_size_text(d['size'])}")
        lines.append(f"  Type:        {_drive_type(d)}")
        if d["wwn"]:
            lines.append(f"  WWN:         {d['wwn']}")
        if d["state"]:
            lines.append(f"  State:       {d['state']}")

        parts = _partitions(d["name"])
        if parts:
            lines.append("  Partitions:")
            for depth, p in parts:
                info = [
                    _short_size(_num(p.get("size"))),
                    p.get("fstype") or "no filesystem",
                ]
                if p.get("label"):
                    info.append(f"label '{p['label']}'")
                if p.get("mountpoint"):
                    info.append(f"mounted at {p['mountpoint']}")
                lines.append(f"    {'  ' * depth}{p.get('name', '?')}: " + ", ".join(info))

        level, text = _smart(f"/dev/{d['name']}")
        lines.append(f"  SMART:       {text}")
        if level:
            levels.append(level)
        lines.append("")

    if "fail" in levels:
        worst = "fail"
    elif "warn" in levels:
        worst = "warn"
    elif levels:
        worst = "pass"
    else:
        worst = "info"
    return worst, "\n".join(lines).rstrip()
