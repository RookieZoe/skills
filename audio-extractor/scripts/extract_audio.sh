#!/bin/bash
set -e

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <input_file>

Extract audio track from video file (lossless copy).

Arguments:
  input_file    Input video file (any FFmpeg-compatible format)

Options:
  -o, --output      Output audio file path (default: same dir, audio extension)
  -f, --format      Force output format: aac, mp3, opus, flac, wav (default: auto-detect)
  -h, --help        Show this help message

Output filename format (when -o not specified):
  {source_name}.{detected_ext}
  Example: video.mp4 → video.aac

Examples:
  $(basename "$0") video.mp4
  $(basename "$0") -o ~/audio/output.aac video.mp4
  $(basename "$0") -f mp3 video.mkv
EOF
    exit 0
}

OUTPUT=""
FORMAT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)  OUTPUT="$2"; shift 2 ;;
        -f|--format)  FORMAT="$2"; shift 2 ;;
        -h|--help)    show_help ;;
        -*)           echo "Unknown option: $1"; exit 1 ;;
        *)            break ;;
    esac
done

if [ $# -lt 1 ]; then
    echo "Error: Missing input file"
    echo "Usage: $(basename "$0") [OPTIONS] <input_file>"
    exit 1
fi

input_file="$1"

if [ ! -f "$input_file" ]; then
    echo "Error: File not found: $input_file"
    exit 1
fi

codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$input_file")

if [ -z "$codec" ]; then
    echo "Error: No audio stream found in $input_file"
    exit 1
fi

if [ -n "$FORMAT" ]; then
    ext="$FORMAT"
    case "$FORMAT" in
        aac|mp3|opus|flac|wav|ogg|m4a) ;;
        *) echo "Warning: Unknown format '$FORMAT', proceeding anyway" ;;
    esac
else
    case "$codec" in
        aac|mp4a) ext="aac" ;;
        mp3)      ext="mp3" ;;
        opus)     ext="opus" ;;
        vorbis)   ext="ogg" ;;
        flac)     ext="flac" ;;
        pcm_*)    ext="wav" ;;
        *)        ext="mka" ;;
    esac
fi

if [ -z "$OUTPUT" ]; then
    base_dir=$(dirname "$input_file")
    base_name=$(basename "$input_file" | sed 's/\.[^.]*$//')
    OUTPUT="${base_dir}/${base_name}.${ext}"
fi

echo "Input:  $input_file"
echo "Codec:  $codec"
echo "Output: $OUTPUT"

ffmpeg -y -i "$input_file" -vn -acodec copy "$OUTPUT" 2>/dev/null

echo "Done: $OUTPUT"
