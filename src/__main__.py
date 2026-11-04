"""Entry point for running the application as a Python zipapp."""

import os
import sys
import tempfile
import zipfile
import tkinter as tk

from app import App


def main():
    asset_dir = None
    archive_path = os.path.abspath(sys.argv[0])
    if zipfile.is_zipfile(archive_path):
        asset_dir = tempfile.TemporaryDirectory(prefix="laptop-test-")
        with zipfile.ZipFile(archive_path) as archive:
            audio = archive.read("Speaker_Test.mp3")
        with open(os.path.join(asset_dir.name, "Speaker_Test.mp3"), "wb") as audio_file:
            audio_file.write(audio)
        os.environ["LAPTOP_TEST_APP_DIR"] = asset_dir.name

    try:
        root = tk.Tk()
        App(root)
        root.mainloop()
    finally:
        if asset_dir is not None:
            asset_dir.cleanup()


if __name__ == "__main__":
    main()