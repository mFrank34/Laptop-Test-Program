"""On-screen keyboard layout data and names for special keys. No GUI code."""


def keyboard_layout():
    """Key positions in key-width units: (label, X11 keycode, x, y, w, h).
    X11 keycodes are physical positions (evdev + 8), so they work on any language layout."""
    items = []

    def row(y, spec, x=0.0):
        for s in spec:
            w = s[2]
            h = s[3] if len(s) > 3 else 1
            if s[0] is not None:
                items.append((s[0], s[1], x, y, w, h))
            x += w

    gap = lambda w: (None, None, w)
    row(
        0,
        [("Esc", 9, 1), gap(1)]
        + [(f"F{i}", c, 1) for i, c in zip(range(1, 5), (67, 68, 69, 70))]
        + [gap(0.5)]
        + [(f"F{i}", c, 1) for i, c in zip(range(5, 9), (71, 72, 73, 74))]
        + [gap(0.5)]
        + [
            ("F9", 75, 1),
            ("F10", 76, 1),
            ("F11", 95, 1),
            ("F12", 96, 1),
            gap(0.5),
            ("PrtSc", 107, 1),
            ("ScrLk", 78, 1),
            ("Pause", 127, 1),
        ],
    )
    row(
        1.5,
        [("`", 49, 1)]
        + [(c, 10 + i, 1) for i, c in enumerate("1234567890")]
        + [("-", 20, 1), ("=", 21, 1), ("Bksp", 22, 2)],
    )
    row(
        2.5,
        [("Tab", 23, 1.5)]
        + [(c, 24 + i, 1) for i, c in enumerate("QWERTYUIOP")]
        + [("[", 34, 1), ("]", 35, 1), ("Enter", 36, 1.5, 2)],
    )
    row(
        3.5,
        [("Caps", 66, 1.5)]
        + [(c, 38 + i, 1) for i, c in enumerate("ASDFGHJKL")]
        + [(";", 47, 1), ("'", 48, 1), ("#", 51, 1)],
    )
    row(
        4.5,
        [("Shift", 50, 1.25), ("\\", 94, 1)]
        + [(c, 52 + i, 1) for i, c in enumerate("ZXCVBNM")]
        + [(",", 59, 1), (".", 60, 1), ("/", 61, 1), ("Shift", 62, 2.75)],
    )
    row(
        5.5,
        [
            ("Ctrl", 37, 1.25),
            ("Win", 133, 1.25),
            ("Alt", 64, 1.25),
            ("", 65, 6.25),
            ("AltGr", 108, 1.25),
            ("Win", 134, 1.25),
            ("Menu", 135, 1.25),
            ("Ctrl", 105, 1.25),
        ],
    )
    row(1.5, [("Ins", 118, 1), ("Home", 110, 1), ("PgUp", 112, 1)], x=15.5)
    row(2.5, [("Del", 119, 1), ("End", 115, 1), ("PgDn", 117, 1)], x=15.5)
    row(4.5, [("\u2191", 111, 1)], x=16.5)
    row(5.5, [("\u2190", 113, 1), ("\u2193", 116, 1), ("\u2192", 114, 1)], x=15.5)
    row(1.5, [("Num", 77, 1), ("/", 106, 1), ("*", 63, 1), ("-", 82, 1)], x=19.5)
    row(2.5, [("7", 79, 1), ("8", 80, 1), ("9", 81, 1), ("+", 86, 1, 2)], x=19.5)
    row(3.5, [("4", 83, 1), ("5", 84, 1), ("6", 85, 1)], x=19.5)
    row(4.5, [("1", 87, 1), ("2", 88, 1), ("3", 89, 1), ("Enter", 104, 1, 2)], x=19.5)
    row(5.5, [("0", 90, 2), (".", 91, 1)], x=19.5)
    return items


# Common Linux input event codes for keys the on-screen layout does not have.
RAW_NAMES = {
    113: "Mute",
    114: "Volume down",
    115: "Volume up",
    116: "Power",
    140: "Calculator",
    141: "Setup",
    142: "Sleep",
    143: "Wake up",
    148: "Program 1",
    149: "Program 2",
    150: "WWW",
    152: "Screen lock",
    155: "Mail",
    161: "Eject",
    163: "Next track",
    164: "Play/Pause",
    165: "Previous track",
    166: "Stop",
    172: "Homepage",
    202: "Program 3",
    203: "Program 4",
    212: "Camera",
    224: "Brightness down",
    225: "Brightness up",
    227: "Switch display",
    228: "Backlight toggle",
    229: "Backlight down",
    230: "Backlight up",
    237: "Bluetooth",
    238: "WLAN",
    247: "RF kill (airplane)",
    248: "Mic mute",
    431: "Display toggle",
    464: "Fn",
    465: "Fn+Esc",
    530: "Touchpad toggle",
    531: "Touchpad on",
    532: "Touchpad off",
}
