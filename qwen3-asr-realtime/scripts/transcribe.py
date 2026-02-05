#!/usr/bin/env python3
"""
CLI for transcribing audio files using Qwen3-ASR Realtime API.

Usage:
    python scripts/transcribe.py --file audio.mp3
    python scripts/transcribe.py --file https://example.com/audio.wav --output /tmp

Required environment variables:
    SKILL__QWEN3_ASR_REALTIME_ENDPOINT - WebSocket endpoint URL
    SKILL__QWEN3_ASR_REALTIME_API_KEY - API key
"""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcription.transcribe import transcribe_file


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Qwen3-ASR Realtime API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Transcribe local file (output to same directory)
    python scripts/transcribe.py --file recording.mp3

    # Transcribe with specific output directory
    python scripts/transcribe.py --file recording.mp3 --output /tmp

    # Transcribe remote URL
    python scripts/transcribe.py --file https://example.com/audio.wav

    # Specify language
    python scripts/transcribe.py --file recording.mp3 --language zh

Environment Variables:
    SKILL__QWEN3_ASR_REALTIME_ENDPOINT - WebSocket endpoint URL
    SKILL__QWEN3_ASR_REALTIME_API_KEY  - API key
        """,
    )

    parser.add_argument(
        "--file",
        "-f",
        required=True,
        help="Audio file path or HTTP URL (supports MP3, WAV, M4A, OGG, AIFF, etc.)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory (default: same dir for local file, ~/Downloads for URL)",
    )

    parser.add_argument(
        "--language",
        "-l",
        default="auto",
        choices=["auto", "zh", "en", "ja", "ko"],
        help="Recognition language (default: auto)",
    )

    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=0.1,
        help="Audio chunk send delay in seconds (default: 0.1)",
    )

    parser.add_argument(
        "--endpoint",
        "-e",
        default=None,
        help="WebSocket endpoint URL (overrides SKILL__QWEN3_ASR_REALTIME_ENDPOINT)",
    )

    parser.add_argument(
        "--api-key",
        "-k",
        default=None,
        help="API key (overrides SKILL__QWEN3_ASR_REALTIME_API_KEY)",
    )

    parser.add_argument(
        "--upload-oss",
        action="store_true",
        help="Upload transcript to OSS (not implemented)",
    )

    parser.add_argument(
        "--resume",
        "-r",
        action="store_true",
        help="Resume from previous run using <output>.resume.json",
    )

    parser.add_argument(
        "--fast",
        nargs="?",
        const="",
        default=None,
        help="Fast mode: --fast for 1s chunks/0.2s delay, --fast X:Y for custom (e.g., --fast 2:0.2)",
    )

    args = parser.parse_args()

    if args.upload_oss:
        print(
            "Error: Upload2OSS not implemented. This feature is planned for future releases.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        output_path = transcribe_file(
            input_file=args.file,
            output_dir=args.output,
            language=args.language,
            delay=args.delay,
            endpoint=args.endpoint,
            api_key=args.api_key,
            verbose=True,
            resume=args.resume,
            fast=args.fast,
        )
        print(f"\nTranscription complete: {output_path}")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)

    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}", file=sys.stderr)
        sys.exit(1)

    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
