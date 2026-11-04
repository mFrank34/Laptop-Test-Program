#!/bin/sh
set -eu

cd "$(dirname "$0")"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT HUP INT TERM

cp -R src/. "$stage/"
cp Speaker_Test.mp3 "$stage/"
find "$stage" -type d -name __pycache__ -prune -exec rm -rf {} +

python3 -m zipapp "$stage" \
    --output laptop-test.pyz \
    --python '/usr/bin/env python3'
chmod +x laptop-test.pyz

printf 'Built executable: %s/laptop-test.pyz\n' "$PWD"