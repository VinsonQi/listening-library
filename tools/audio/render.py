#!/usr/bin/env python3
"""Render fresh, natural-speed English audio using local Kokoro neural TTS."""
import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL_URL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx'
VOICES_URL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin'
MODEL_SHA256 = 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a'
VOICES_SHA256 = 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'

def sha256(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--script', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--work-dir', type=Path, required=True, help='Stores intermediate paragraph WAVs')
    p.add_argument('--voice', default='af_heart')
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--minimum-seconds', type=float, default=600)
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    a.work_dir.mkdir(parents=True, exist_ok=True)
    script = a.script.read_text(encoding='utf-8')
    paragraphs = [x.strip() for x in re.split(r'\n\s*\n', script) if x.strip()]
    if not paragraphs:
        p.error('The narration script is empty')
    model = a.model_dir / 'kokoro-v1.0.onnx'
    voices = a.model_dir / 'voices-v1.0.bin'
    for file, expected in [(model, MODEL_SHA256), (voices, VOICES_SHA256)]:
        if sha256(file) != expected:
            raise ValueError(f'Model asset checksum mismatch: {file}')
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = a.threads
    opts.inter_op_num_threads = 1
    session = ort.InferenceSession(str(model), sess_options=opts, providers=['CPUExecutionProvider'])
    engine = Kokoro.from_session(session, str(voices))
    parts, records, elapsed = [], [], 0.0
    started = time.time()
    for i, paragraph in enumerate(paragraphs):
        # Spoken forms of project names and verified terms; display transcript is unchanged.
        spoken = paragraph.replace('CPlantBox', 'C Plant Box').replace('DuMuX', 'Doo mooks')
        # Verified long-eye vowel in biome; display transcript is unchanged.
        # NHS Genomics: https://www.genomicseducation.hee.nhs.uk/glossary/microbiome/
        spoken = re.sub(r'\bmicrobiome\b', 'micro-biome', spoken, flags=re.IGNORECASE)
        t = time.time()
        samples, sr = engine.create(spoken, voice=a.voice, speed=1.0, lang='en-us',
                                    sentence_pause=0.25, clause_pause=0.1)
        if sr != 24000 or not np.isfinite(samples).all() or len(samples) == 0:
            raise ValueError(f'Invalid audio in paragraph {i + 1}')
        sf.write(a.work_dir / f'paragraph-{i + 1:02}.wav', samples, sr)
        record = {'index': i + 1, 'text': paragraph, 'spokenText': spoken,
                  'startSeconds': round(elapsed, 3), 'durationSeconds': round(len(samples) / sr, 3),
                  'words': len(paragraph.split())}
        records.append(record)
        parts.append(samples)
        elapsed += len(samples) / sr
        if i < len(paragraphs) - 1:
            # Normal breathing room at a paragraph boundary, never runtime padding.
            pause = np.zeros(round(sr * 0.35), dtype=np.float32)
            parts.append(pause)
            elapsed += len(pause) / sr
        print(json.dumps({'paragraph': i + 1, 'total': len(paragraphs),
                          'audioSeconds': record['durationSeconds'],
                          'generationSeconds': round(time.time() - t, 2),
                          'totalAudioSeconds': round(elapsed, 2)}), flush=True)
    samples = np.concatenate(parts)
    master = a.output_dir / 'audio-master.wav'
    output = a.output_dir / 'audio.mp3'
    sf.write(master, samples, sr, subtype='PCM_24')
    # Loudness normalization and encoding only. No tempo, atempo, or stretch filter.
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(master), '-af',
                    'loudnorm=I=-19:TP=-2:LRA=11', '-ar', '24000', '-ac', '1',
                    '-c:a', 'libmp3lame', '-b:a', '128k', str(output)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                                               '-show_streams', '-of', 'json', str(output)]))
    duration = float(probe['format']['duration'])
    report = {'voice': a.voice, 'model': 'Kokoro-82M v1.0, full-precision ONNX',
              'engine': f"kokoro-onnx {importlib.metadata.version('kokoro-onnx')}",
              'modelSource': MODEL_URL, 'voiceSource': VOICES_URL,
              'modelSHA256': MODEL_SHA256, 'voicesSHA256': VOICES_SHA256,
              'pronunciationLexicon': [{'displayText': 'microbiome', 'spokenText': 'micro-biome',
                  'reference': 'https://www.genomicseducation.hee.nhs.uk/glossary/microbiome/',
                  'referencePronunciation': 'mahy-kroh-bahy-ohm'}],
              'speed': 1.0, 'sampleRate': sr, 'channels': 1, 'bitRate': 128000,
              'wordCount': len(script.split()), 'durationSeconds': duration,
              'pcmDurationSeconds': len(samples) / sr, 'runtimeSeconds': time.time() - started,
              'scriptSHA256': hashlib.sha256(script.encode()).hexdigest(),
              'mp3SHA256': sha256(output), 'peakAmplitudeBeforeNormalization': float(np.abs(samples).max()),
              'rmsBeforeNormalization': float(np.sqrt(np.mean(samples ** 2))),
              'paragraphPauseSeconds': 0.35, 'silencePadding': False, 'timeStretching': False,
              'meetsMinimumDuration': duration >= a.minimum_seconds,
              'paragraphs': records}
    (a.output_dir / 'audio-generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'paragraphs'}, indent=2), flush=True)
    if not report['meetsMinimumDuration']:
        raise SystemExit('Narration is too short. Expand the substantive script, then regenerate; never pad or slow the audio.')

if __name__ == '__main__':
    main()
