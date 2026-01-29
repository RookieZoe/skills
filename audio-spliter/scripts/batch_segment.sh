#!/bin/bash
set -e

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <input> <segment_seconds>

Batch segment media files into audio chunks with silence-aware cut points.

Modes:
  Single file:  $(basename "$0") video.mp4 1800
  Batch:        $(basename "$0") -d ./videos 1800

Arguments:
  input             Input file or directory (with -d flag)
  segment_seconds   Target segment duration in seconds (e.g., 1800 = 30 min)

Options:
  -d, --dir         Treat input as directory for batch processing
  --depth           Directory traversal depth (default: 3, use with -d)
  -w, --window      Search window ±N seconds around target (default: 10)
  -n, --noise       Silence detection threshold (default: -60dB)
  -s, --silence     Minimum silence duration in seconds (default: 2)
  -o, --output-dir  Output directory (default: input file's directory)
  -h, --help        Show this help message

Supported formats (auto-detected):
  Video: mp4, mkv, avi, mov, webm, flv, wmv, m4v
  Audio: mp3, aac, flac, wav, ogg, opus, m4a, wma

Output filename format:
  {source_name}_{num}_[{start}-{end}].{ext}

Examples:
  # Single file
  $(basename "$0") video.mp4 1800
  $(basename "$0") -w 15 -n "-35dB" lecture.mkv 2700

  # Batch processing
  $(basename "$0") -d ./lectures 1800
  $(basename "$0") -d ./podcasts --depth 5 -o ./output 3600
EOF
    exit 0
}

WINDOW_SIZE=10
NOISE_THRESHOLD="-60dB"
SILENCE_DURATION=2
OUTPUT_DIR=""
BATCH_MODE=false
MAX_DEPTH=3

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)          BATCH_MODE=true; shift ;;
        --depth)           MAX_DEPTH="$2"; shift 2 ;;
        -w|--window)       WINDOW_SIZE="$2"; shift 2 ;;
        -n|--noise)        NOISE_THRESHOLD="$2"; shift 2 ;;
        -s|--silence)      SILENCE_DURATION="$2"; shift 2 ;;
        -o|--output-dir)   OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)         show_help ;;
        -*)                echo "Unknown option: $1"; exit 1 ;;
        *)                 break ;;
    esac
done

if [ $# -lt 2 ]; then
    echo "Error: Missing required arguments"
    echo "Usage: $(basename "$0") [OPTIONS] <input> <segment_seconds>"
    exit 1
fi

input_path="$1"
segment_duration="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

process_single_file() {
    local input_file="${1}"
    local out_dir="${OUTPUT_DIR:-$(dirname "${input_file}")}"

    echo ""
    echo "========================================"
    echo "Processing: ${input_file}"
    echo "========================================"

    "${SCRIPT_DIR}/segment_audio.sh" \
        -w "${WINDOW_SIZE}" \
        -n "${NOISE_THRESHOLD}" \
        -s "${SILENCE_DURATION}" \
        -o "${out_dir}" \
        "${input_file}" "${segment_duration}"

    echo "=== File done! ==="
}

if [ "${BATCH_MODE}" = true ]; then
    if [ ! -d "${input_path}" ]; then
        echo "Error: Directory not found: ${input_path}"
        exit 1
    fi

    echo "=== Batch Processing Mode ==="
    echo "Directory: ${input_path}"
    echo "Depth: ${MAX_DEPTH}"
    echo "Segment duration: ${segment_duration}s"
    echo ""

    file_count=0
    success_count=0
    fail_count=0

    while IFS= read -r file; do
        [ -z "${file}" ] && continue
        ((file_count++)) || true
        if process_single_file "${file}"; then
            ((success_count++)) || true
        else
            ((fail_count++)) || true
            echo "Warning: Failed to process ${file}"
        fi
    done < <(find "${input_path}" -maxdepth "${MAX_DEPTH}" -type f \( \
        -iname "*.mp4" -o -iname "*.mkv" -o -iname "*.avi" -o -iname "*.mov" \
        -o -iname "*.webm" -o -iname "*.flv" -o -iname "*.wmv" -o -iname "*.m4v" \
        -o -iname "*.mp3" -o -iname "*.aac" -o -iname "*.flac" -o -iname "*.wav" \
        -o -iname "*.ogg" -o -iname "*.opus" -o -iname "*.m4a" -o -iname "*.wma" \
    \) 2>/dev/null)

    echo ""
    echo "========================================"
    echo "=== Batch Processing Complete ==="
    echo "Total files: ${file_count}"
    echo "Success: ${success_count}"
    echo "Failed: ${fail_count}"
    echo "========================================"
else
    if [ ! -f "${input_path}" ]; then
        echo "Error: File not found: ${input_path}"
        echo "Hint: Use -d flag for directory batch processing"
        exit 1
    fi

    process_single_file "${input_path}"
    echo ""
    echo "=== All done! ==="
fi
