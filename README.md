# 🛠️ Alpine Hardware Diagnostic Suite (Quick Hardware Test)

A lightweight, self-contained live Linux environment engineered specifically for rapid bare-metal hardware testing and bench diagnostics. Built on top of Alpine Linux, it runs an interactive Python (Tkinter) interface directly in RAM for fast, reliable, and non-destructive hardware verification.

---

## ✨ Features

- **Keyboard Test:** Verify key press responses and layouts interactively.
- **Mouse & Touchpad Test:** Check clicks, scrolling performance, and tracking precision.
- **Display Test:** Screen for dead pixels, backlight bleed, and color accuracy with full-screen test patterns.
- **Audio & Speaker Test:** Validate output clarity and playback channel balance.
- **Webcam Preview:** Fast video stream verification using `ffmpeg`.
- **USB Device Monitoring:** Real-time detection and hotplug chimes for connected peripherals via `lsusb`.
- **Device / Driver Audit:** Opens a side window that detects keyboard, mouse/touchpad, and ALSA audio presence, then reports PCI/USB devices without a bound kernel driver using Linux `/proc` and `/sys` interfaces. It flags devices for functional follow-up; detection alone does not verify operation.

---

## 📦 System & Package Dependencies

The diagnostic tool utilizes only the **Python 3 Standard Library** (`tkinter`), requiring no external PyPI packages. However, the system relies on standard Linux utilities for multimedia and device control.

### Required Alpine Packages

Include the following packages in your Alpine Linux build setup (`apks`):

```bash
# Core Python & UI runtime
apk add python3 py3-tkinter

# Multimedia & Hardware integration
apk add ffmpeg            # Webcam preview & audio playback backend
apk add alsa-utils        # Speaker test & USB connection chime (`aplay`)
apk add usbutils          # Real-time USB monitoring (`lsusb`)

# Optional audio fallback
apk add pulseaudio-utils  # Optional fallback if PulseAudio is configured (`paplay`)
```

---

## 🚀 Usage & Deployment

### Running unit tests

From the project directory, run the hardware-independent tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

### Running standard Python source
To execute the diagnostic tool in your environment:

```bash
python3 hwtest_gui.py
```

### Running as a Zipapp (`.pyz`)
If using the bundled standalone package:

```bash
python3 laptop-test.pyz
```

---

## 🔨 Building Standalone Executables (Optional)

The script automatically detects frozen environments (`sys.frozen`), making it fully compatible with **PyInstaller** if you prefer a single binary build.

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole hwtest_gui.py
```

---

## 💿 ISO Live Environment Booting

1. Flash the compiled `alpine-hwtest-3.24-x86_64.iso` to a USB drive using **Ventoy**, **Rufus**, or `dd`.
2. Boot the target machine into the USB live environment.
3. The interactive diagnostic suite launches automatically upon system boot.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.