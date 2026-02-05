---
name: audio-spliter
description: "Split media files (video/audio) into audio segments by duration with silence-aware cut points using FFmpeg. Use when users need to segment long recordings, podcasts, lectures, or videos into chunks. Supports batch processing and any FFmpeg-compatible format."
allowed-tools: [Bash(ffmpeg, ffprobe, bc, grep, sed, find)]
---

# Audio Splitter

Segment media files into audio chunks with intelligent silence detection for clean cut points.

## Quick Start

```bash
# Single file (video or audio)
./scripts/segment_audio.sh video.mp4 1800

# Batch processing
./scripts/batch_segment.sh -d ./videos 1800
```

## Scripts

| Script | Purpose |
|--------|---------|
| `segment_audio.sh` | Segment single file (video or audio) |
| `batch_segment.sh` | Batch wrapper for multiple files |

## segment_audio.sh

Segment a single media file into audio chunks.

```bash
./scripts/segment_audio.sh [OPTIONS] <input_file> <segment_seconds>
```

| Option | Default | Description |
|--------|---------|-------------|
| `-w, --window` | 10 | Search window ±N seconds |
| `-n, --noise` | -60dB | Silence threshold (dBFS) |
| `-s, --silence` | 2 | Min silence duration (seconds) |
| `-o, --output-dir` | input dir | Output directory |

**Examples:**
```bash
./scripts/segment_audio.sh video.mp4 1800              # 30-min segments
./scripts/segment_audio.sh podcast.mp3 1800
./scripts/segment_audio.sh -w 15 -n "-35dB" lecture.mkv 2700
```

## batch_segment.sh (Batch)

Batch process multiple files in a directory.

```bash
./scripts/batch_segment.sh -d [OPTIONS] <input_dir> <segment_seconds>
```

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --dir` | - | Enable batch mode |
| `--depth` | 3 | Directory traversal depth |
| `-w, --window` | 10 | Search window ±N seconds |
| `-n, --noise` | -60dB | Silence threshold |
| `-s, --silence` | 2 | Min silence duration |
| `-o, --output-dir` | input dir | Output directory |

**Examples:**
```bash
./scripts/batch_segment.sh -d ./lectures 1800
./scripts/batch_segment.sh -d ./podcasts --depth 5 3600
./scripts/batch_segment.sh -d ./videos -o ./output 1800
```

## Output Format

`{source_name}_{num}_[{start}-{end}].{ext}`

Example: `video.mp4` → `video_01_[0-1800].aac`, `video_02_[1800-3595].aac`

## Supported Formats

- **Video**: mp4, mkv, avi, mov, webm, flv, wmv, m4v
- **Audio**: mp3, aac, flac, wav, ogg, opus, m4a, wma

## Detection Settings

| Audio Type | Noise | Window | Silence |
|------------|-------|--------|---------|
| Quiet studio | -50dB | 5s | 0.5s |
| **Default** | -60dB | 10s | 2s |
| Noisy recording | -35dB | 15s | 1.5s |

## Dependencies

- FFmpeg with ffprobe (`brew install ffmpeg`)
