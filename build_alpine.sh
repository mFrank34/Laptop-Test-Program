#!/bin/sh
set -eu

cd "$(dirname "$0")"

apk add --no-cache \
    python3 \
    py3-tkinter \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev \
    patchelf

build_env="${TMPDIR:-/tmp}/laptop-test-pyinstaller"
python3 -m venv "$build_env"
"$build_env/bin/python" -m pip install --upgrade pip pyinstaller

"$build_env/bin/pyinstaller" \
    --clean \
    --noconfirm \
    --onefile \
    --windowed \
    --name laptop-test \
    --add-data "Speaker_Test.mp3:." \
    test_gui.py

printf '\nBuilt executable: %s/dist/laptop-test\n' "$PWD"