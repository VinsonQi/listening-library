# Fresh neural narration for Listening Library

This folder is the reproducible audio production recipe. It contains no old lesson audio, model cache, virtual environment, credentials, or paid-service dependency.

## Runtime

Tested with Python 3.12.14 on Linux x86-64 and ffmpeg/ffprobe 7.1.5. The pinned Python packages come from PyPI. Kokoro-82M v1.0 is an 82-million-parameter neural text-to-speech model. The selected voice is `af_heart` (American English). The full-precision model and voice pack come from the official kokoro-onnx release assets, whose URLs and SHA-256 checksums are embedded in the renderer and setup script.

The `espeakng-loader` library is used only for text-to-phoneme conversion. The audible waveform is synthesized by the Kokoro neural model. This is not an eSpeak voice and is not Apple `say`.

## One-time preparation

Use a work directory outside the Site repository. The virtual environment needs roughly 150 MB and the model assets roughly 350 MB. `ffmpeg` and `ffprobe` must already be installed or installed from a reputable OS package source.

```sh
bash tools/audio/setup.sh /workspace/shared/listening-audio-work
```

Model assets:

- https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
- https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin

Sources and licenses:

- Engine source and MIT license: https://github.com/thewh1teagle/kokoro-onnx
- Kokoro model source and Apache 2.0 model license: https://huggingface.co/hexgrad/Kokoro-82M
- Voice documentation: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

## Render a new lesson

Write a new source-grounded script of approximately 1,900 words in a plain-text file. Use blank lines to separate natural paragraphs. Do not include headings, citations, or production directions unless they should be spoken. Model speed is fixed at 1.0. Every run synthesizes fresh paragraph audio; it does not reuse prior recordings.

```sh
/workspace/shared/listening-audio-work/.venv/bin/python tools/audio/render.py \
  --script /workspace/shared/new-lesson/script.txt \
  --output-dir /workspace/shared/new-lesson \
  --model-dir /workspace/shared/listening-audio-work/models \
  --work-dir /workspace/shared/listening-audio-work/new-lesson-paragraphs
```

Outputs:

- `audio.mp3`: 24 kHz, mono, 128 kbps, normalized to a -19 LUFS target with a -2 dBTP ceiling
- `audio-master.wav`: 24-bit PCM master
- `audio-generation.json`: measured durations, hashes, model provenance, paragraph timing, and generation configuration

The renderer gives each paragraph a normal 0.35-second breath, preserves punctuation, and never applies time stretching or adds filler to reach a duration. If the MP3 is shorter than 600 seconds, it exits with a clear message. Expand the substantive script and regenerate rather than slowing or padding it. The displayed transcript remains the exact written script; CPlantBox, DuMuX, and the verified term microbiome have explicit spoken-form substitutions. The microbiome mapping uses “micro-biome” in the TTS input to obtain the long-eye vowel in biome; the visible script is unchanged. Pronunciation reference: https://www.genomicseducation.hee.nhs.uk/glossary/microbiome/.

The first 1,895-word lesson rendered to 725.352 seconds (12:05) of MP3 in 256.8 seconds on a 4-thread CPU session, including encoding. Runtime varies with hardware and contention.

## Quality assurance before publishing

1. Decode the whole MP3 with ffmpeg and confirm there are no decoder errors
2. Confirm `ffprobe` reports a real duration of at least 600 seconds and the intended audio format
3. Inspect beginning, middle, and end for intelligible, complete speech and correct ordering
4. Check clipping and prolonged silence; investigate any long silent gaps
5. Match the script hash to the transcript and retain the generation report
6. Publish only the final new audio and its corresponding transcript/lesson metadata; do not ship caches or the WAV master unless needed

Optional automated transcription checks can use faster-whisper. The first lesson was checked using the public Systran/faster-whisper-base.en model, running locally on CPU. With PyAV 19, avoid the older `metadata_errors` argument by decoding via ffmpeg into a 16 kHz mono float32 array before passing the array to `WhisperModel.transcribe`.
