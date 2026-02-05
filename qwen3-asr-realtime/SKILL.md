---
name: qwen3-asr-realtime
description: "Transcribe local or HTTP audio/video files using DashScope SDK + qwen3-asr-flash-realtime. Outputs {source}-文字稿.txt. Provides CLI and importable module interface."
allowed-tools: [Python]
---

# Qwen3-ASR-Realtime

Transcribe audio/video files to text using Alibaba DashScope's qwen3-asr-flash-realtime model.

## Quick Start

1. Enter the skill directory and run `uv sync` to install dependencies:

```bash
cd /path/to/qwen3-asr-realtime
uv sync
```

2. You can run the CLI from any directory, but you must use the absolute path to the venv Python and script:

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file ./video.mp4 --fast 3:0.2
```

> **Note:** Replace `/path/to/qwen3-asr-realtime` with your actual skill directory path.

## CLI Usage

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file <input_file>
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file https://example.com/audio.mp3
```

### Modes

**Realtime mode** (default): Simulates real-time playback speed

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3
```

**Fast mode**: Process audio faster than real-time. `--fast` overrides `--delay` when both specified.

```bash
# Default fast (1s chunks, 0.2s delay)
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3 --fast

# Custom fast (2s chunks, 0.2s delay)
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3 --fast 2:0.2
```

**Resume mode**: Continue from interruption using `.resume.json`

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3 --resume
```

## Module Usage

```python
from transcription.transcribe import transcribe_file

result = transcribe_file("audio.mp3")
```

## Output

- `{source_name}-文字稿.txt` in same directory as input
- Resume state saved to `{source_name}-文字稿.txt.resume.json`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SKILL__QWEN3_ASR_REALTIME_ENDPOINT` | Yes | DashScope ASR endpoint |
| `SKILL__QWEN3_ASR_REALTIME_API_KEY` | Yes | DashScope API key |

## Supported Formats

- **Audio**: mp3, wav, flac, aac, ogg, m4a
- **Video**: mp4, mkv, avi, mov, webm (audio track extracted)

## Dependencies

- Python 3.10+
- FFmpeg (`brew install ffmpeg`)
- pydub (for audio processing)
- dashscope (for ASR API)

## Usage Scenarios

**Long videos** (fast mode for speed):

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file long_video.mp4 --fast
```

**Interrupted runs** (resume from where it stopped):

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3 --resume
```

**Realtime parity** (default behavior, matches audio duration):

```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file audio.mp3
```
