"""
transcription_skill.transcribe - Core transcription logic using DashScope SDK

Provides file-based transcription using Qwen3-ASR Realtime API.
Supports local files and HTTP URLs, with automatic format conversion.
"""

import base64
import json
import os
import tempfile
import time
from urllib.parse import urlparse

import dashscope
from dashscope.audio.qwen_omni import (
    MultiModality,
    OmniRealtimeCallback,
    OmniRealtimeConversation,
)
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams

# ==================== Constants ====================

MODEL_NAME = "qwen3-asr-flash-realtime"
ENV_ENDPOINT = "SKILL__QWEN3_ASR_REALTIME_ENDPOINT"
ENV_API_KEY = "SKILL__QWEN3_ASR_REALTIME_API_KEY"


# ==================== Fast Mode ====================


def parse_fast_arg(value: str | None) -> tuple[float, float, str]:
    """
    Parse --fast argument value.

    Args:
        value: None (flag not present), '' (flag present, no value), or 'X:Y'

    Returns:
        Tuple of (chunk_seconds, delay_seconds, mode)

    Raises:
        ValueError: If format is invalid
    """
    # No --fast flag: realtime mode (0.1s chunks, 0.1s delay)
    if value is None:
        return (0.1, 0.1, "realtime")

    # --fast with no value: default fast mode (1.0s chunks, 0.2s delay)
    if value == "":
        return (1.0, 0.2, "fast")

    # --fast X:Y format
    if ":" not in value:
        raise ValueError(
            f"Invalid --fast format: '{value}'. Expected 'X:Y' (e.g., '2:0.2')"
        )

    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid --fast format: '{value}'. Expected 'X:Y' (e.g., '2:0.2')"
        )

    try:
        chunk_seconds = float(parts[0])
        delay_seconds = float(parts[1])
    except ValueError:
        raise ValueError(
            f"Invalid --fast values: '{value}'. Both X and Y must be numbers."
        )

    if chunk_seconds <= 0 or delay_seconds < 0:
        raise ValueError(
            f"Invalid --fast values: chunk must be > 0, delay must be >= 0"
        )

    return (chunk_seconds, delay_seconds, "fast")


# ==================== Callback ====================


class ASRCallback(OmniRealtimeCallback):
    """Realtime transcription callback handler."""

    def __init__(self, output_path: str, input_file: str, verbose: bool = True):
        self.output_path = output_path
        self.input_file = input_file
        self.confirmed_text = ""
        self.stash_text = ""
        self.is_running = True
        self.verbose = verbose
        self.bytes_sent = 0
        self.segments_written = 0

    def _write_resume_json(self):
        """Write resume state to sidecar JSON file."""
        resume_path = f"{self.output_path}.resume.json"
        resume_data = {
            "version": 1,
            "input_file": self.input_file,
            "bytes_sent": self.bytes_sent,
            "segments_written": self.segments_written,
        }
        with open(resume_path, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2)

    def update_bytes_sent(self, bytes_count: int):
        self.bytes_sent = bytes_count

    def on_open(self):
        if self.verbose:
            print("\n[+] Connected")

    def on_close(self, close_status_code, close_msg):
        if self.verbose:
            print(
                f"\n[-] Connection closed, code: {close_status_code}, msg: {close_msg}"
            )
        self.is_running = False

    def on_event(self, message):
        if isinstance(message, str):
            response = json.loads(message)
        else:
            response = message
        event_type = response.get("type", "")

        # Session created
        if event_type == "session.created":
            session_id = response.get("session", {}).get("id", "unknown")
            if self.verbose:
                print(f"[i] Session created: {session_id}")

        # Session updated
        elif event_type == "session.updated":
            if self.verbose:
                print("[i] Session configured")

        # Realtime transcription result
        elif event_type == "conversation.item.input_audio_transcription.text":
            text = response.get("text", "")
            stash = response.get("stash", "")

            # Update confirmed text
            if text:
                self.confirmed_text = text
            self.stash_text = stash

            # Display progress
            if self.verbose:
                display_text = text + stash
                print(f"\r[~] {display_text[:80]}...", end="", flush=True)

        # Final transcription result
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = response.get("transcript", "")
            self.confirmed_text += transcript
            self.stash_text = ""

            # Write segment immediately to file (append mode)
            with open(self.output_path, "a", encoding="utf-8") as f:
                f.write(transcript + "\n\n")

            self.segments_written += 1
            self._write_resume_json()

            if self.verbose:
                print(f"\n[+] Segment: {transcript[:60]}...")

        # Session finished
        elif event_type == "session.finished":
            if self.verbose:
                print("\n[+] Session finished")
            self.is_running = False

        # Error
        elif event_type == "error":
            error = response.get("error", {})
            print(f"\n[!] Error: {error.get('message', 'Unknown error')}")


# ==================== Audio Processing ====================


def is_remote_url(path: str) -> bool:
    """Check if path is a remote HTTP/HTTPS URL."""
    try:
        parsed = urlparse(path)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def download_remote_audio(url: str, timeout: int = 60) -> str:
    """
    Download remote audio file to temp directory.

    Args:
        url: Remote audio file URL
        timeout: Download timeout in seconds

    Returns:
        Temporary file path
    """
    import urllib.error
    import urllib.request

    print(f"[>] Downloading: {url}")

    # Extract file extension from URL
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1] or ".wav"

    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix=ext, prefix="asr_")
    os.close(fd)

    try:
        # Set request headers (simulate browser)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        request = urllib.request.Request(url, headers=headers)

        # Download file
        with urllib.request.urlopen(request, timeout=timeout) as response:
            total_size = response.headers.get("Content-Length")
            if total_size:
                total_size = int(total_size)
                print(f"    Size: {total_size / 1024 / 1024:.2f} MB")

            # Write to temp file
            with open(temp_path, "wb") as f:
                downloaded = 0
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = downloaded / total_size * 100
                        print(f"\r    Progress: {progress:.1f}%", end="", flush=True)

        print(f"\n[+] Downloaded: {temp_path}")
        return temp_path

    except urllib.error.HTTPError as e:
        os.unlink(temp_path)
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        os.unlink(temp_path)
        raise RuntimeError(f"URL error: {e.reason}")
    except Exception as e:
        os.unlink(temp_path)
        raise RuntimeError(f"Download failed: {e}")


def convert_audio_to_pcm(input_path: str) -> str:
    """
    Convert any audio format to PCM (16kHz, 16-bit, mono).

    Supported formats: MP3, WAV, M4A, OGG, FLAC, AAC, AIFF, etc.

    Args:
        input_path: Input audio file path

    Returns:
        Converted PCM file path (temp file)

    Requires:
        pip install pydub
        ffmpeg must be installed system-wide
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise RuntimeError(
            "pydub is required for audio conversion: pip install pydub\n"
            "ffmpeg must also be installed: apt install ffmpeg or brew install ffmpeg"
        )

    print("[>] Converting to PCM (16kHz, 16-bit, mono)...")

    try:
        # Load audio file (pydub auto-detects format)
        audio = AudioSegment.from_file(input_path)

        # Convert parameters
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio = audio.set_sample_width(2)  # 16-bit
        audio = audio.set_channels(1)  # mono

        # Export to raw PCM
        fd, pcm_path = tempfile.mkstemp(suffix=".pcm", prefix="asr_")
        os.close(fd)

        # Export as raw PCM format
        audio.export(pcm_path, format="s16le", parameters=["-ar", "16000", "-ac", "1"])

        duration = len(audio) / 1000  # ms to seconds
        print(f"[+] Converted: {duration:.1f}s, {os.path.getsize(pcm_path)} bytes")

        return pcm_path

    except Exception as e:
        raise RuntimeError(f"Audio conversion failed: {e}")


def read_audio_chunks(file_path: str, chunk_size: int = 3200):
    """Read audio file in chunks (3200 bytes = 0.1s PCM16/16kHz)."""
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


def send_audio_file(
    conversation,
    file_path: str,
    delay: float = 0.1,
    start_offset: int = 0,
    callback=None,
    chunk_size_bytes: int = 3200,
):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    chunk_seconds = chunk_size_bytes / 16000 / 2
    print(f"[>] Sending audio: {file_path}")
    if start_offset > 0:
        print(f"    Resuming from byte offset: {start_offset}")
    print(f"    Chunk: {chunk_seconds:.2f}s ({chunk_size_bytes} bytes), Delay: {delay}s")
    print("    Press Ctrl+C to stop\n")

    total_bytes = start_offset
    start_time = time.time()

    with open(file_path, "rb") as f:
        if start_offset > 0:
            f.seek(start_offset)
        while chunk := f.read(chunk_size_bytes):
            audio_b64 = base64.b64encode(chunk).decode("ascii")
            conversation.append_audio(audio_b64)
            total_bytes += len(chunk)
            if callback:
                callback.update_bytes_sent(total_bytes)
            time.sleep(delay)

    elapsed = time.time() - start_time
    print(f"\n[+] Sent: {total_bytes} bytes in {elapsed:.1f}s")


# ==================== Main Transcription ====================


def get_output_path(input_source: str, output_dir: str | None = None) -> str:
    """
    Determine output file path based on input source.

    Args:
        input_source: Input file path or URL
        output_dir: Optional output directory override

    Returns:
        Full output file path with -transcript.txt suffix
    """
    if is_remote_url(input_source):
        # Remote URL: extract basename from path
        parsed = urlparse(input_source)
        source_name = os.path.splitext(os.path.basename(parsed.path))[0]
        if not source_name:
            source_name = "remote-audio"
        out_dir = output_dir or os.path.expanduser("~/Downloads")
    else:
        # Local file
        source_name = os.path.splitext(os.path.basename(input_source))[0]
        out_dir = output_dir or os.path.dirname(os.path.abspath(input_source))

    return os.path.join(out_dir, f"{source_name}-文字稿.txt")


def transcribe_file(
    input_file: str,
    output_dir: str | None = None,
    language: str = "auto",
    delay: float = 0.1,
    endpoint: str | None = None,
    api_key: str | None = None,
    verbose: bool = True,
    resume: bool = False,
    fast: str | None = None,
) -> str:
    """
    Transcribe an audio file and save result to text file.

    Args:
        input_file: Local file path or HTTP URL
        output_dir: Output directory (default: same dir for local, ~/Downloads for URL)
        language: Recognition language ('auto', 'zh', 'en', 'ja', 'ko')
        delay: Audio chunk send delay in seconds (ignored if fast is set)
        endpoint: WebSocket endpoint (overrides env var)
        api_key: API key (overrides env var)
        verbose: Print progress messages
        resume: If True, resume from previous run using <output>.resume.json
        fast: Fast mode value - None (realtime), '' (default fast), or 'X:Y'

    Returns:
        Path to output transcript file

    Raises:
        RuntimeError: If endpoint/api_key not configured
        FileNotFoundError: If input file not found
    """
    # Check local file exists early (before env var checks for better UX)
    if not is_remote_url(input_file) and not os.path.exists(input_file):
        raise FileNotFoundError(f"Audio file not found: {input_file}")

    # Get configuration from env or arguments
    ws_url = endpoint or os.environ.get(ENV_ENDPOINT)
    api_key = api_key or os.environ.get(ENV_API_KEY)

    if not ws_url:
        raise RuntimeError(
            f"Endpoint not configured. Set {ENV_ENDPOINT} environment variable "
            "or pass --endpoint argument."
        )
    if not api_key:
        raise RuntimeError(
            f"API key not configured. Set {ENV_API_KEY} environment variable "
            "or pass --api-key argument."
        )

    # Set API key for DashScope
    dashscope.api_key = api_key

    # Parse fast mode settings
    chunk_seconds, actual_delay, mode = parse_fast_arg(fast)
    chunk_size_bytes = int(chunk_seconds * 16000 * 2)

    # Determine output path
    output_path = get_output_path(input_file, output_dir)

    if verbose:
        print("=" * 60)
        print("[*] Transcription Service")
        print("=" * 60)
        print(f"    Endpoint: {ws_url}")
        print(f"    Input: {input_file}")
        print(f"    Output: {output_path}")
        print(f"    Language: {language}")
        print(f"    Mode: {mode} (chunk={chunk_seconds}s, delay={actual_delay}s)\n")

    # Track temp files for cleanup
    temp_file = None
    pcm_file = None
    local_audio_file = input_file

    # Download if remote URL
    if is_remote_url(input_file):
        temp_file = download_remote_audio(input_file)
        local_audio_file = temp_file

    # Convert to PCM if needed
    file_ext = os.path.splitext(local_audio_file)[1].lower()
    if file_ext != ".pcm":
        try:
            pcm_file = convert_audio_to_pcm(local_audio_file)
            local_audio_file = pcm_file
        except Exception as e:
            # Cleanup downloaded file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            raise RuntimeError(f"Audio conversion failed: {e}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    start_offset = 0
    resume_path = f"{output_path}.resume.json"
    if resume and os.path.exists(resume_path):
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                resume_data = json.load(f)
            start_offset = resume_data.get("bytes_sent", 0)
            if verbose:
                print(f"[i] Resuming from byte offset: {start_offset}")
        except (json.JSONDecodeError, KeyError) as e:
            if verbose:
                print(f"[!] Could not read resume file, starting fresh: {e}")

    # Initialize conversation
    callback = None
    conversation = None

    try:
        # Create callback
        callback = ASRCallback(
            output_path=output_path,
            input_file=input_file,
            verbose=verbose,
        )
        callback.bytes_sent = start_offset

        # Create conversation
        conversation = OmniRealtimeConversation(
            model=MODEL_NAME, url=ws_url, callback=callback
        )

        # Configure transcription params
        if language == "auto":
            transcription_params = TranscriptionParams(
                sample_rate=16000, input_audio_format="pcm"
            )
        else:
            transcription_params = TranscriptionParams(
                language=language, sample_rate=16000, input_audio_format="pcm"
            )

        # Connect
        conversation.connect()

        # Configure session (Manual mode: no VAD)
        conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_turn_detection=False,
            enable_input_audio_transcription=True,
            transcription_params=transcription_params,
        )

        # Wait for session configuration
        time.sleep(1)

        # Send audio
        send_audio_file(
            conversation,
            local_audio_file,
            actual_delay,
            start_offset,
            callback,
            chunk_size_bytes,
        )

        # Commit for recognition (Manual mode)
        if verbose:
            print("\n[>] Committing for recognition...")
        conversation.commit()

        # Wait for recognition
        time.sleep(3)

        # End session
        if verbose:
            print("[>] Ending session...")
        conversation.end_session()

        # Wait for result
        timeout = 30
        start = time.time()
        while callback.is_running and time.time() - start < timeout:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
    finally:
        if conversation is not None:
            conversation.close()

        # Cleanup temp files
        for tmp in [pcm_file, temp_file]:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except Exception:
                    pass

        if (pcm_file or temp_file) and verbose:
            print("[i] Cleaned up temp files")

    # Get final transcript
    transcript = callback.confirmed_text if callback else ""

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"[*] Transcript ({len(transcript)} chars):")
        print(f"{'=' * 60}")
        print(transcript[:500] + ("..." if len(transcript) > 500 else ""))
        print(f"{'=' * 60}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if verbose:
        print(f"\n[+] Saved to: {output_path}")

    return output_path
