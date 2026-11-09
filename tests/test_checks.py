import struct
import unittest
from unittest.mock import patch

from checks import battery, drives, system, webcam
from windows.raw_input import _EVENT_FMT, parse_key_events


class BatteryCheckTests(unittest.TestCase):
    def test_battery_grade_boundaries(self):
        self.assertEqual(battery.battery_grade(80), "EXCELLENT")
        self.assertEqual(battery.battery_grade(60), "GOOD")
        self.assertEqual(battery.battery_grade(50), "FAIR")
        self.assertEqual(battery.battery_grade(49.9), "POOR")

    def test_capacity_health_uses_matching_energy_files(self):
        values = {
            "/fake/BAT0/status": "Discharging",
            "/fake/BAT0/cycle_count": "120",
            "/fake/BAT0/energy_full": "75000000",
            "/fake/BAT0/energy_full_design": "100000000",
            "/fake/BAT0/capacity": "42",
        }

        def fake_glob(pattern):
            if pattern.endswith("BAT*"):
                return ["/fake/BAT0"]
            return []

        with patch.object(battery.glob, "glob", side_effect=fake_glob), patch.object(
            battery, "read", side_effect=lambda path: values.get(path)
        ):
            status, report = battery.check_battery()

        self.assertEqual(status, "pass")
        self.assertIn("Health: 75.0%  (GOOD)", report)
        self.assertIn("Current charge: 42%", report)

    def test_missing_battery_is_informational(self):
        with patch.object(battery.glob, "glob", return_value=[]):
            status, report = battery.check_battery()

        self.assertEqual(status, "info")
        self.assertIn("No battery detected", report)


class DriveHelperTests(unittest.TestCase):
    def test_flag_and_size_formatting(self):
        self.assertTrue(drives._flag(True))
        self.assertTrue(drives._flag("1"))
        self.assertFalse(drives._flag("false"))
        self.assertEqual(drives._size_text(0), "unknown")
        self.assertEqual(drives._short_size(500_000_000), "500 MB")

    def test_drive_type_identifies_nvme_and_removable(self):
        disk = {
            "tran": "nvme",
            "rota": False,
            "removable": True,
        }
        self.assertEqual(drives._drive_type(disk), "NVMe SSD (removable)")


class SystemAndInputTests(unittest.TestCase):
    def test_added_usb_devices_reports_only_new_lines(self):
        added = system.added_usb_devices("device A\ndevice B", "device B\ndevice C")
        self.assertEqual(added, ["device C"])

    def test_raw_keyboard_events_include_only_key_press(self):
        key_press = struct.pack(_EVENT_FMT, 0, 0, 1, 30, 1)
        key_release = struct.pack(_EVENT_FMT, 0, 0, 1, 30, 0)
        mouse_button = struct.pack(_EVENT_FMT, 0, 0, 1, 0x110, 1)

        self.assertEqual(parse_key_events(key_press + key_release + mouse_button), [30])

    def test_webcam_check_reports_no_camera(self):
        with patch.object(webcam.glob, "glob", return_value=[]):
            status, report = webcam.check_webcam()

        self.assertEqual(status, "fail")
        self.assertIn("No camera detected", report)


if __name__ == "__main__":
    unittest.main()