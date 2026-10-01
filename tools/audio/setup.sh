#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:?Usage: setup.sh /absolute/path/to/audio-work}"
mkdir -p "$WORK/models"
python3 -m venv "$WORK/.venv"
"$WORK/.venv/bin/python" -m pip install -r "$HERE/requirements.txt"
curl --fail --location --retry 2 --output "$WORK/models/kokoro-v1.0.onnx" 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx'
curl --fail --location --retry 2 --output "$WORK/models/voices-v1.0.bin" 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin'
printf '%s  %s\n' 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a' "$WORK/models/kokoro-v1.0.onnx" 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d' "$WORK/models/voices-v1.0.bin" | sha256sum --check
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
