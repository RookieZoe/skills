---
name: audio-extractor
description: "Extract audio tracks from video files using FFmpeg (lossless copy). Use when users need to extract audio from video without splitting or segmentation. Supports any FFmpeg-compatible format."
allowed-tools: [Bash(ffmpeg, ffprobe)]
---

# Audio Extractor

Extract audio track from video files without re-encoding (lossless).

## Quick Start

```bash
./scripts/extract_audio.sh video.mp4              # → video.aac
./scripts/extract_audio.sh -o output.aac video.mp4
./scripts/extract_audio.sh -f mp3 video.mkv       # Force MP3 format
```

## Usage

```bash
./scripts/extract_audio.sh [OPTIONS] <input_file>
```

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | auto | Output file path |
| `-f, --format` | auto | Force format: aac, mp3, opus, flac, wav |

## Output

- Default: `{source_name}.{detected_ext}` in same directory
- Auto-detects codec: AAC→.aac, MP3→.mp3, Opus→.opus, FLAC→.flac

## Supported Formats

- **Input**: mp4, mkv, avi, mov, webm, flv, wmv, m4v
- **Output**: aac, mp3, opus, ogg, flac, wav, mka

## Dependencies

- FFmpeg with ffprobe (`brew install ffmpeg`)
