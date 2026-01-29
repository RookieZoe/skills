#!/bin/bash
set -e

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <input_file> <segment_seconds>

Segment media file into audio chunks with silence-aware cut points.

Arguments:
  input_file        Input media file (video or audio, any FFmpeg format)
  segment_seconds   Target segment duration in seconds (e.g., 1800 = 30 min)

Options:
  -w, --window      Search window ±N seconds around target (default: 10)
  -n, --noise       Silence detection threshold (default: -60dB)
  -s, --silence     Minimum silence duration in seconds (default: 2)
  -o, --output-dir  Output directory (default: input file's directory)
  -h, --help        Show this help message

Output filename format:
  {source_name}_{num}_[{start}-{end}].{ext}
  Example: video_01_[0-1800].aac, video_02_[1800-3595].aac

Examples:
  $(basename "$0") video.mp4 1800
  $(basename "$0") podcast.mp3 1800
  $(basename "$0") -w 15 -n "-35dB" lecture.mkv 2700
EOF
    exit 0
}

WINDOW_SIZE=10
NOISE_THRESHOLD="-60dB"
SILENCE_DURATION=2
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
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
    echo "Usage: $(basename "$0") [OPTIONS] <input_file> <segment_seconds>"
    exit 1
fi

input_file="${1}"
segment_duration="${2}"
OUTPUT_DIR="${OUTPUT_DIR:-$(dirname "${input_file}")}"
base_name=$(basename "${input_file}" | sed 's/\.[^.]*$//')

if [ ! -f "${input_file}" ]; then
    echo "Error: File not found: ${input_file}"
    exit 1
fi

codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "${input_file}" < /dev/null)
case "${codec}" in
    aac|mp4a) ext="aac" ;;
    mp3)      ext="mp3" ;;
    opus)     ext="opus" ;;
    vorbis)   ext="ogg" ;;
    flac)     ext="flac" ;;
    *)        ext="mka" ;;
esac

total_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${input_file}" < /dev/null | cut -d. -f1)

echo "Input: ${input_file}"
echo "Duration: ${total_duration}s, Codec: ${codec}, Segment target: ${segment_duration}s"
echo "Output: ${OUTPUT_DIR}/${base_name}_*.${ext}"
echo ""

segment_count=$(( (total_duration + segment_duration - 1) / segment_duration ))

find_silence_point() {
    local target_time=${1}
    local window_start=$((target_time - WINDOW_SIZE))
    local window_end=$((target_time + WINDOW_SIZE))

    [ ${window_start} -lt 0 ] && window_start=0
    [ ${window_end} -gt ${total_duration} ] && window_end=${total_duration}

    local silence_output=$(ffmpeg -i "${input_file}" -ss "${window_start}" -to "${window_end}" \
        -af "silencedetect=noise=${NOISE_THRESHOLD}:duration=${SILENCE_DURATION}" \
        -f null - < /dev/null 2>&1 | grep -E "silence_start|silence_end" | head -2)

    local silence_start=$(echo "${silence_output}" | grep "silence_start" | head -1 | sed -n 's/.*silence_start: \([0-9.]*\).*/\1/p')
    local silence_end=$(echo "${silence_output}" | grep "silence_end" | head -1 | sed -n 's/.*silence_end: \([0-9.]*\).*/\1/p')

    if [ -n "${silence_start}" ] && [ -n "${silence_end}" ]; then
        local abs_start=$(echo "${window_start} + ${silence_start}" | bc)
        local abs_end=$(echo "${window_start} + ${silence_end}" | bc)
        local midpoint=$(echo "scale=3; (${abs_start} + ${abs_end}) / 2" | bc)
        echo "${midpoint}"
    else
        echo ""
    fi
}

cut_points=(0)
for ((i=1; i<segment_count; i++)); do
    target_time=$((segment_duration * i))

    [ ${target_time} -ge ${total_duration} ] && break

    silence_point=$(find_silence_point ${target_time})

    if [ -n "${silence_point}" ]; then
        echo "Segment ${i}: Found silence at ${silence_point}s (target: ${target_time}s)"
        cut_points+=("${silence_point}")
    else
        echo "Segment ${i}: No silence found, using target ${target_time}s"
        cut_points+=("${target_time}")
    fi
done

cut_points+=("${total_duration}")

echo ""
echo "Cut points: ${cut_points[*]}"
echo ""

mkdir -p "${OUTPUT_DIR}"
for ((i=0; i<${#cut_points[@]}-1; i++)); do
    start=${cut_points[$i]}
    end=${cut_points[$((i+1))]}
    segment_num=$(printf '%02d' $((i + 1)))
    start_int=${start%.*}
    end_int=${end%.*}
    output_file="${OUTPUT_DIR}/${base_name}_${segment_num}_[${start_int}-${end_int}].${ext}"

    echo "Extracting segment $((i+1)): ${start}s to ${end}s -> ${output_file}"
    ffmpeg -y -i "${input_file}" -ss "${start}" -to "${end}" -vn -acodec copy "${output_file}" < /dev/null 2>/dev/null
done

echo ""
echo "Done! Created $((${#cut_points[@]} - 1)) segments."
