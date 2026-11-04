"""Speaker test: decode 'Speaker Test.mp3' with ffmpeg and play it with aplay."""

import os
import shutil
import subprocess
import tempfile

from utils import app_dir


def play_speakers():
    if not shutil.which("ffmpeg"):
        return "warn", "FFmpeg is not installed."

    if not shutil.which("aplay"):
        return "warn", "aplay is not installed. Run: sudo apt install alsa-utils"

    path = os.path.join(app_dir(), "Speaker_Test.mp3")
    if not os.path.isfile(path):
        return "fail", f"MP3 not found:\n{path}"

    wav = None
    try:
        # Create a unique temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            wav = temp.name

        # Convert MP3 to WAV
        decoded = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", path,
             "-f", "wav", "-acodec", "pcm_s16le", wav],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if decoded.returncode != 0:
            return "fail", f"FFmpeg error:\n{decoded.stderr}"

        if not os.path.isfile(wav) or os.path.getsize(wav) == 0:
            return "fail", "The converted audio file is empty."

        # Play the WAV file
        result = subprocess.run(
            ["aplay", "-q", wav], capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return "fail", f"ALSA playback error:\n{result.stderr}"

        return "pass", "Speaker test completed successfully!"

    except subprocess.TimeoutExpired as e:
        return "fail", f"Audio operation timed out: {e.cmd}"
    except Exception as e:
        return "fail", f"Audio error: {e}"
    finally:
        # Always remove the temporary WAV
        if wav and os.path.exists(wav):
            try:
                os.unlink(wav)
            except OSError:
                pass
