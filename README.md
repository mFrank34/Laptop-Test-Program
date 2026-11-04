# Laptop-Test-Program
An Application for Testing Laptop for self container ISO Image


```
src/
├── main.py                  # entry point (the __main__ block)
├── app.py                   # App class: main window, badge, output box, run_all, save
├── theme.py                 # KEY_IDLE/HELD/DONE, COLORS
├── utils.py                 # read(), run()
│
├── checks/                  # pure functions returning (status, text)
│   ├── battery.py           # battery_grade, _capacity, _friendly, _raw_attributes, check_battery
│   ├── system.py            # check_summary, check_usb, shutdown
│   ├── webcam.py            # check_webcam (the quick /dev/video check)
│   └── speakers.py          # play_speakers
│
└── windows/                 # Tkinter Toplevel windows
    ├── keyboard_layout.py   # _keyboard_layout(), RAW_NAMES
    ├── raw_input.py         # parse_key_events, raw_key_listener
    ├── keyboard.py          # keyboard_window
    ├── mouse.py             # mouse_window
    ├── screen.py            # screen_window
    └── webcam.py            # find_cameras, build_ffmpeg_cmd, _frame_reader, webcam_window
```