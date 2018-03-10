#! /usr/bin/env bash
# Create screencaps for a video file
# Works with the ffprobe JSON format. Both ffprobe and ffmpeg need to be
# installed.
#
# Usage patterns:
#
# $ screencap file
# Default annotations are generalized from the file using ffprobe.
#
# $ screencap file < json
# Annotations are extracted from json format
#
# $ screencap [-i file and other ffmpeg options]
# This allows fine-tuning ffmpeg parameters, but no annotations
#
# $ screencap [-i file and other ffmpeg options] < json
# Most flexible and best option
#

: ${FFMPEG=ffmpeg -nostdin} ${FFPROBE=ffprobe}
set -e
export TMPDIR="$(mktemp -d -t $$.XXXXXXXX)"
intermediate="$(mktemp -t XXXXXXXX.png)"

type ionice &> /dev/null && FFMPEG="ionice -n 7 $FFMPEG"

if [[ -t 2 ]]
then
  FFMPEG="${FFMPEG} -loglevel warning"
  FFPROBE="${FFPROBE} -loglevel warning"
fi

declare -a convert_args ffmpeg_args
if [[ $# -eq 1 ]]
then
  input_path="$@"
  [[ -f "$input_path" ]]
  ffmpeg_args+=( -i )
  ffmpeg_args+=( "${input_path}" )
else
  ffmpeg_args=( "$@" )
fi

if [[ -t 0 ]]
then
  [[ $input_path ]] && json_info=$($FFPROBE -show_format -show_streams -show_chapters -print_format json "$input_path")
else
  json_info=$(cat)
  input_path=$(jq -r ".format.filename?" <<< "$json_info")
fi

if [[ $json_info ]]
then
  if ! [[ $title ]]
  then
    if jq -e ".format.tags?.title?" <<< "$json_info"
    then
    title=$(jq -r .format.tags.title <<< "$json_info")
    else
    title="${input_path##*/}"
    fi > /dev/null
  fi
  bit_rate=$(jq ".format.bit_rate | tonumber | . / 1E6" <<< "$json_info")
  [[ $duration ]] || duration=$(jq ".format.duration? | tonumber" <<< "$json_info")
  megapixels=$(jq '.streams[] | select(.codec_type == "video") | .width * .height / 1E6' <<< "$json_info")
  file_size=$(jq '.format.size | tonumber' <<< "$json_info")

  [[ $title ]] &&
    convert_args+=( -gravity northwest -annotate +0+0 "$title" )
  [[ $megapixels ]] && [[ $bit_rate ]] && 
    convert_args+=( -gravity northeast -annotate +0+0 "$megapixels Mpx @ $bit_rate Mbit" )
  duration_t=$(jq -r ".format.duration_t?" <<< "$json_info")
  [[ $duration_t ]] || duration_t="$duration s"
  [[ $duration_t ]] &&
    convert_args+=( -gravity southwest -annotate +0+0 "$duration_t" )
  file_size_t=$(jq -r ".format.size_t?" <<< "$json_info")
  [[ $file_size_t ]] || file_size_t="$file_size bytes"
  [[ $file_size_t ]] &&
    convert_args+=( -gravity southeast -annotate +0+0 "$file_size_t" )
fi

[[ $output ]] || output="${title}.jpeg"
# This ffmpeg isn't happy doing 4K video tiled beyond n=30
if ! [[ $seconds_between ]]
then
  [[ $duration ]] && seconds_between=$(awk "BEGIN {print ${duration-900} / 31}")
fi
if $FFMPEG -skip_frame nokey -an -vsync 0 -y "${ffmpeg_args[@]}" \
  -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,${seconds_between-30})',tile=3x10" \
  -frames:v 1 \
  "$intermediate"
then
  [[ -s "$intermediate" ]]
  output_folder=$(dirname "$output")
  [[ $output_folder ]] && [[ -d "$output_folder" ]] || mkdir -p "$output_folder"
  convert "$intermediate" -resize '2000000@>' \
    -fill gray95 -undercolor '#00000080' \
    -font Palatino-Bold -pointsize 28 -antialias \
    "${convert_args[@]}" "$output"
fi
