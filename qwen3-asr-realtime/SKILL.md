---
name: qwen3-asr-realtime
description: "Transcribe local or HTTP audio/video files using DashScope SDK + qwen3-asr-flash-realtime. Outputs {source}-文字稿.txt. Provides CLI and importable module interface."
allowed-tools: [Python]
---

# Qwen3-ASR-Realtime

Transcribe audio/video files to text using Alibaba DashScope's qwen3-asr-flash-realtime model.

## Quick Start

```bash
uv sync
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file ./video.mp4 --fast
```

## CLI Usage

### Flags
- `-f, --file`: Audio file path(s), URL(s), or directory. (Required)
- `-o, --output`: Output directory (default: same as input or ~/Downloads).
- `-l, --language`: Recognition language (auto, zh, en, ja, ko). Default: auto.
- `--fast [X:Y]`: Fast mode (1s chunks, 0.2s delay). Custom with X:Y.
- `-d, --delay`: Audio chunk send delay in seconds. Default: 0.1.
- `-r, --resume`: Resume from previous run using .resume.json.
- `--max-concurrency`: Max concurrent transcriptions for batch processing. Default: 2.
- `-e, --endpoint`: WebSocket endpoint URL (overrides env var).
- `-k, --api-key`: DashScope API key (overrides env var).

### Examples

**Single File**
```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file https://example.com/audio.mp3 --language en
```

**Batch Processing**
```bash
/path/to/qwen3-asr-realtime/.venv/bin/python /path/to/qwen3-asr-realtime/scripts/transcribe.py --file ./audio_dir --max-concurrency 4 --fast 2:0.2
```

## Output
- `{source_name}-文字稿.txt` in same directory as input
- Resume state saved to `{source_name}-文字稿.txt.resume.json`

## Environment Variables
| Variable | Description |
|----------|-------------|
| `SKILL__QWEN3_ASR_REALTIME_ENDPOINT` | DashScope ASR WebSocket endpoint |
| `SKILL__QWEN3_ASR_REALTIME_API_KEY` | DashScope API key |

## Supported Formats
- **Audio**: mp3, wav, flac, aac, ogg, m4a
- **Video**: mp4, mkv, avi, mov, webm (audio track extracted)

## Dependencies
- Python 3.10+
- FFmpeg (`brew install ffmpeg`)
- pydub, dashscope
