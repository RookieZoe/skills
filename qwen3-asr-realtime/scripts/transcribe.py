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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcription.transcribe import transcribe_file


# ==================== Batch Processing Functions ====================

# Supported audio/video formats
SUPPORTED_FORMATS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".m4a",
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
}


def collect_files_from_inputs(inputs: List[str]) -> List[str]:
    """
    Collect files from input list (files, URLs, or directories).

    Args:
        inputs: List of file paths, URLs, or directory paths

    Returns:
        List of file paths/URLs, sorted by basename (stable sort with full path tiebreaker)
    """
    collected = []

    for input_item in inputs:
        # Skip URLs - pass through directly
        if input_item.startswith(("http://", "https://")):
            collected.append(input_item)
            continue

        # Handle directories - collect files from top level only
        if os.path.isdir(input_item):
            dir_path = Path(input_item)
            for file_path in dir_path.iterdir():
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in SUPPORTED_FORMATS
                ):
                    collected.append(str(file_path))
        # Handle regular files
        elif os.path.isfile(input_item):
            collected.append(input_item)
        else:
            # File doesn't exist - will be handled during processing
            collected.append(input_item)

    # Stable sort: primary key = basename, secondary key = full path
    def sort_key(path: str) -> Tuple[str, str]:
        if path.startswith(("http://", "https://")):
            # For URLs, use the last path component as basename
            basename = path.split("/")[-1] if "/" in path else path
            return (basename, path)
        else:
            return (os.path.basename(path), path)

    return sorted(collected, key=sort_key)


def process_batch(
    files: List[str],
    output_dir: str | None,
    language: str,
    delay: float,
    endpoint: str | None,
    api_key: str | None,
    resume: bool,
    fast: str | None,
    max_concurrency: int,
) -> Tuple[List[str], List[Tuple[str, str]], List[str]]:
    """
    Process multiple files concurrently with error handling.

    Args:
        files: List of file paths or URLs to process
        output_dir: Output directory
        language: Recognition language
        delay: Audio chunk send delay
        endpoint: WebSocket endpoint
        api_key: API key
        resume: Resume from previous run
        fast: Fast mode value
        max_concurrency: Maximum concurrent transcriptions

    Returns:
        Tuple of (successful_files, failed_files_with_errors, skipped_files)
    """
    successful = []
    failed = []
    skipped = []

    def process_single_file(file_path: str) -> Tuple[str, str | None, str | None]:
        """
        Process a single file and return result.

        Returns:
            Tuple of (file_path, output_path_or_none, error_message_or_none)
        """
        try:
            output_path = transcribe_file(
                input_file=file_path,
                output_dir=output_dir,
                language=language,
                delay=delay,
                endpoint=endpoint,
                api_key=api_key,
                verbose=False,  # Disable verbose for batch mode
                resume=resume,
                fast=fast,
            )
            return (file_path, output_path, None)
        except Exception as e:
            return (file_path, None, str(e))

    # Process files concurrently
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_single_file, f): f for f in files}

        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path, output_path, error = future.result()

            if error is None:
                successful.append(file_path)
                print(f"✓ {file_path} → {output_path}")
            else:
                failed.append((file_path, error))
                print(f"✗ {file_path}: {error}", file=sys.stderr)

    return successful, failed, skipped


def print_summary(
    successful: List[str],
    failed: List[Tuple[str, str]],
    skipped: List[str],
) -> None:
    """
    Print batch processing summary.

    Args:
        successful: List of successfully processed files
        failed: List of (file_path, error_message) tuples
        skipped: List of skipped files
    """
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)

    total = len(successful) + len(failed) + len(skipped)
    print(f"Total files: {total}")
    print(f"  ✓ Success: {len(successful)}")
    print(f"  ✗ Failed:  {len(failed)}")
    print(f"  ⊘ Skipped: {len(skipped)}")

    if failed:
        print(f"\nFailed files:")
        for file_path, error in failed:
            print(f"  - {file_path}: {error}")

    if skipped:
        print(f"\nSkipped files:")
        for file_path in skipped:
            print(f"  - {file_path}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Qwen3-ASR Realtime API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Transcribe single local file (output to same directory)
    python scripts/transcribe.py --file recording.mp3

    # Transcribe with specific output directory
    python scripts/transcribe.py --file recording.mp3 --output /tmp

    # Transcribe remote URL
    python scripts/transcribe.py --file https://example.com/audio.wav

    # Specify language
    python scripts/transcribe.py --file recording.mp3 --language zh
    
    # Batch processing: transcribe multiple files
    python scripts/transcribe.py --file audio1.mp3 audio2.wav audio3.m4a
    
    # Batch with custom concurrency
    python scripts/transcribe.py --file file1.mp3 file2.mp3 --max-concurrency 4
    
    # Process all files in a directory
    python scripts/transcribe.py --file /path/to/audio_dir
    
    # Mix files and URLs (both local and remote)
    python scripts/transcribe.py --file local.mp3 https://example.com/remote.wav

Environment Variables:
    SKILL__QWEN3_ASR_REALTIME_ENDPOINT - WebSocket endpoint URL
    SKILL__QWEN3_ASR_REALTIME_API_KEY  - API key
        """,
    )

    parser.add_argument(
        "--file",
        "-f",
        nargs="+",
        required=True,
        help="Audio file path(s) or HTTP URL(s) (supports MP3, WAV, M4A, OGG, AIFF, etc.). Can specify multiple files.",
    )

    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Maximum number of concurrent transcriptions for batch processing (default: 2)",
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

    # Validate max_concurrency
    if args.max_concurrency < 1:
        print(
            f"Warning: Invalid --max-concurrency value ({args.max_concurrency}). Using default value of 2.",
            file=sys.stderr,
        )
        args.max_concurrency = 2

    # Detect mixed inputs: directory + (file or URL)
    has_directory = any(
        os.path.isdir(f) for f in args.file if not f.startswith(("http://", "https://"))
    )
    has_file_or_url = any(
        not os.path.isdir(f) if not f.startswith(("http://", "https://")) else True
        for f in args.file
    )

    if has_directory and has_file_or_url and len(args.file) > 1:
        print(
            "Error: Cannot mix directory input with file/URL inputs. Use either directories OR files/URLs, not both.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.upload_oss:
        print(
            "Error: Upload2OSS not implemented. This feature is planned for future releases.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect all files from inputs (handles directories, files, URLs)
    files = collect_files_from_inputs(args.file)

    # Handle empty directory case
    if not files:
        print("No supported audio/video files found in the specified directory.")
        sys.exit(0)

    # Single file mode - use existing logic for backward compatibility
    if len(files) == 1:
        try:
            output_path = transcribe_file(
                input_file=files[0],
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

    # Batch mode - process multiple files
    print(
        f"Processing {len(files)} file(s) with concurrency={args.max_concurrency}...\n"
    )

    try:
        successful, failed, skipped = process_batch(
            files=files,
            output_dir=args.output,
            language=args.language,
            delay=args.delay,
            endpoint=args.endpoint,
            api_key=args.api_key,
            resume=args.resume,
            fast=args.fast,
            max_concurrency=args.max_concurrency,
        )

        print_summary(successful, failed, skipped)

        # Exit code: 0 if all succeed, 1 if any fail
        if failed:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
