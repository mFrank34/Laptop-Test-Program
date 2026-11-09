import os
import tempfile
import unittest

from checks.devices import check_devices, detect_input_devices


class DeviceCheckTests(unittest.TestCase):
    def test_detects_input_audio_and_unbound_devices(self):
        with tempfile.TemporaryDirectory() as root:
            proc_root = os.path.join(root, "proc")
            sys_root = os.path.join(root, "sys")
            input_path = os.path.join(proc_root, "bus", "input", "devices")
            audio_path = os.path.join(proc_root, "asound", "cards")
            pci_path = os.path.join(sys_root, "bus", "pci", "devices", "0000:00:01.0")
            usb_path = os.path.join(sys_root, "bus", "usb", "devices", "1-1")
            os.makedirs(os.path.dirname(input_path))
            os.makedirs(os.path.dirname(audio_path))
            os.makedirs(pci_path)
            os.makedirs(usb_path)
            with open(input_path, "w", encoding="utf-8") as file:
                file.write(
                    'I: Bus=0011\nN: Name="Built-in keyboard"\nH: Handlers=sysrq kbd event0\n\n'
                    'I: Bus=0003\nN: Name="USB Optical Mouse"\nH: Handlers=mouse0 event1\n'
                )
            with open(audio_path, "w", encoding="utf-8") as file:
                file.write(" 0 [PCH            ]: HDA-Intel - HDA Intel PCH")
            with open(os.path.join(usb_path, "product"), "w", encoding="utf-8") as file:
                file.write("USB Test Device")

            status, report = check_devices(proc_root, sys_root)
            inputs = detect_input_devices(proc_root)

        self.assertEqual(status, "warn")
        self.assertIn("Keyboard: detected", report)
        self.assertIn("needs functional testing", report)
        self.assertIn("Mouse / Touchpad: detected", report)
        self.assertIn("Audio: detected", report)
        self.assertIn("USB: USB Test Device", report)
        self.assertIn("Devices without a bound driver: 2", report)
        self.assertEqual(inputs["keyboard"], ["Built-in keyboard"])
        self.assertEqual(inputs["mouse / touchpad"], ["USB Optical Mouse"])

    def test_warns_when_expected_devices_are_absent(self):
        with tempfile.TemporaryDirectory() as root:
            status, report = check_devices(root, root)
            inputs = detect_input_devices(root)

        self.assertEqual(status, "warn")
        self.assertIn("Keyboard: NOT DETECTED", report)
        self.assertIn("Mouse / Touchpad: NOT DETECTED", report)
        self.assertIn("Audio: NOT DETECTED", report)
        self.assertIn("Missing expected devices", report)
        self.assertIn("needs further inspection", report)
        self.assertEqual(inputs, {"keyboard": [], "mouse / touchpad": []})


if __name__ == "__main__":
    unittest.main()