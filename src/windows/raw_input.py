"""Raw /dev/input reader (needs root). Sees keys the desktop ignores, like Fn and media keys."""

import glob
import os
import select
import struct

from utils import read

_EVENT_FMT = "llHHi"
_EVENT_SIZE = struct.calcsize(_EVENT_FMT)


def parse_key_events(data):
    """Return Linux key codes from raw input_event bytes (key presses only, no mouse buttons)."""
    codes = []
    for i in range(0, len(data) - _EVENT_SIZE + 1, _EVENT_SIZE):
        _s, _u, etype, code, value = struct.unpack(
            _EVENT_FMT, data[i : i + _EVENT_SIZE]
        )
        if etype == 1 and value == 1 and not 0x100 <= code < 0x160:
            codes.append(code)
    return codes


def raw_key_listener(out_q, stop):
    """Runs in a thread. Puts ('info', text) and ('key', code, device) on out_q until stop is set."""
    fds = {}
    for path in glob.glob("/dev/input/event*"):
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
        fds[fd] = read(f"/sys/class/input/{os.path.basename(path)}/device/name") or path
    if not fds:
        out_q.put(("info", "No readable input devices found."))
        return
    out_q.put(
        ("info", f"Raw listener running on {len(fds)} input devices. Press any key.")
    )
    try:
        while not stop.is_set():
            ready, _, _ = select.select(list(fds), [], [], 0.2)
            for fd in ready:
                try:
                    data = os.read(fd, _EVENT_SIZE * 32)
                except OSError:
                    continue
                for code in parse_key_events(data):
                    out_q.put(("key", code, fds[fd]))
    finally:
        for fd in fds:
            os.close(fd)
