---
name: audio-spliter
description: Extract and split audio from media files using FFmpeg with intelligent silence detection. Use when users need to (1) extract audio tracks from video/audio files, (2) split long media into segments by duration, (3) find optimal cut points at silence gaps, or (4) batch process media files with smart segmentation. Supports any FFmpeg-compatible format (mp4, mkv, avi, mov, mp3, flac, wav, ogg, etc.).
allowed-tools: [Bash(ffmpeg, ffprobe, bc, grep, sed)]
---

# Audio Splitter

Extract audio from media files and split into segments with intelligent silence detection for clean cut points. Perfect for splitting podcasts, lectures, or long recordings into manageable chunks.

## Quick Start

```bash
# Split video into 30-minute audio segments
./scripts/split_audio.sh "podcast.mp4" 1800

# Split with custom silence detection
./scripts/split_audio.sh -w 15 -n "-35dB" "lecture.mp3" 2700
```

## Features

- **Silence Detection**: Find optimal cut points at natural pauses
- **Lossless Extraction**: Copy audio stream without re-encoding
- **Smart Segmentation**: Target duration with silence-aware adjustments
- **Format Agnostic**: Any FFmpeg-compatible video/audio format
- **Automatic Codec Detection**: Output matches source codec

## Supported Formats

- **Video**: mp4, mkv, avi, mov, webm, flv, wmv
- **Audio**: mp3, aac, flac, wav, ogg, opus, m4a

## CLI Usage

```bash
# Basic: 30-minute segments
./scripts/split_audio.sh "input.mp4" 1800

# Custom silence detection (±15s window, -35dB threshold)
./scripts/split_audio.sh -w 15 -n "-35dB" "input.mp4" 1800

# Custom output directory
./scripts/split_audio.sh -o ./output "input.mp4" 1800

# Show help
./scripts/split_audio.sh --help
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `input_file` | Input media file | Required |
| `segment_seconds` | Target segment duration (seconds) | Required |
| `-w, --window` | Search window ±N seconds around target | 10 |
| `-n, --noise` | Silence threshold (dBFS) | -40dB |
| `-s, --silence` | Minimum silence duration (seconds) | 0.5 |
| `-o, --output-dir` | Output directory | Input file's dir |
| `-h, --help` | Show help message | - |

### Output Format

`{source_name}_{num}_[{start}-{end}].{ext}`

Example: `podcast.mp4` → `podcast_01_[0-1800].aac`, `podcast_02_[1800-3595].aac`

## Examples

### Split 3-Hour Podcast into 50-Minute Chapters

```bash
./scripts/split_audio.sh "episode.mp4" 3000
# Output:
#   episode_01_[0-3000].aac
#   episode_02_[3000-6000].aac
#   episode_03_[6000-9000].aac
#   episode_04_[9000-10800].aac
```

### Split Lecture with Wider Search Window

```bash
# Search ±30 seconds for silence (good for lectures with long pauses)
./scripts/split_audio.sh -w 30 -s 1 "lecture.mp3" 1800
```

### Extract and Split to Specific Directory

```bash
./scripts/split_audio.sh -o ~/Desktop/chapters "interview.mkv" 1200
```

## Manual Operations

### Probe Media Info

```bash
ffprobe "input.mp4"
```

### Extract Audio Only (No Split)

```bash
ffmpeg -i "input.mp4" -vn -acodec copy "output.aac"
```

### Detect Silence Points

```bash
ffmpeg -i "input.mp4" -af "silencedetect=noise=-40dB:duration=0.5" -f null - 2>&1 | grep -E "(silence_start|silence_end)"
```

## Detection Settings Guide

| Audio Type | Noise Threshold | Window | Min Silence | Notes |
|------------|-----------------|--------|-------------|-------|
| Quiet studio | -50dB | 5s | 0.3s | Very sensitive |
| Normal podcast | -40dB | 10s | 0.5s | Default |
| Noisy recording | -35dB | 15s | 1.0s | Less sensitive |
| Live recording | -30dB | 20s | 1.5s | Audience noise |

### Adjusting Sensitivity

- **More precise cuts**: Lower threshold (-50dB), shorter silence (0.3s)
- **Fewer cuts**: Higher threshold (-30dB), longer silence (1.5s)
- **Natural breaks**: Wider window (20-30s)

## Dependencies

- FFmpeg with ffprobe (`brew install ffmpeg` on macOS)

## Limitations

- Works best with speech content
- Very noisy recordings may need threshold adjustment
- Cut points are approximate (within search window)
- No chapter naming (manual rename if needed)
