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
# $ screencap file [ffmpeg options]
# This allows fine-tuning ffmpeg parameters
#
# Variables observed:
#  duration			Override detection of video duration
#  edit_from		Specify a file to hold JSON probe results and edit it
#  output			Image file to write
#  seconds_between	Number of seconds between screen captures

: ${FFMPEG=ffmpeg -nostdin} ${FFPROBE=ffprobe}
set -e
export TMPDIR="$(mktemp -d -t $$.XXXXXXXX)"
intermediate="$(mktemp -t XXXXXXXX.png)"

type ionice &> /dev/null && FFMPEG="ionice -n 7 $FFMPEG"
type ionice &> /dev/null && FFPROBE="ionice -n 7 $FFPROBE"

if [[ -t 2 ]]; then
  FFMPEG="${FFMPEG} -loglevel warning"
  FFPROBE="${FFPROBE} -loglevel warning"
fi

declare -a convert_args ffmpeg_args

# defaults
# This ffmpeg isn't happy doing 4K video tiled beyond n=30
layout=3x10
while getopts "ei:s:" flag
do
  case "$flag" in
    e) edit_from="$(mktemp -t XXXXXXXX.json)" ;;
	i) ;; # pass through for ffmpeg compatibility
    s) layout="$OPTARG" ;;
    :)
      echo "Usage: -$flag requires an argument"
      exit 10
      ;;
    #\?) # literal '?'
    #*) # Should not occur
  esac
done >&2
shift $((OPTIND-1))

ffmpeg_args+=( -i )
if [[ $# -eq 1 ]]; then
  input_path="$@"
  [[ -f "$input_path" ]]
  ffmpeg_args+=( "${input_path}" )
else
  ffmpeg_args+=( "$@" )
fi


if [[ -t 0 ]]; then
  [[ -s $input_path ]] && probe_json=$($FFPROBE -show_format -show_streams -show_chapters -print_format json "$input_path")
else
  probe_json=$(jq -c .) # capture stdin and check it
  input_path=$(jq -r ".format.filename?" <<< "$probe_json")
fi

if [[ $edit_from ]]; then
  if ! [[ -s "$edit_from" ]]; then
    insert_screencap_defaults <<< "$probe_json" > "$edit_from"
  fi
  $VISUAL "$edit_from"
  json_info=$(jq -c . < "$edit_from")
else
  json_info=$(insert_screencap_defaults <<< "$probe_json")
fi

[[ $output ]] || output="${input_path##*/}.jpeg"
# duration is needed to calculate interval between screen captures
[[ $duration ]] || duration=$(jq ".format.duration? | tonumber" <<< "$json_info")

title=$(jq -r '.title? // .format.tags?.title?' <<< "$json_info") && title=$(basename "$title")
[[ $title != null ]] &&
  convert_args+=( -gravity northwest -annotate +0+0 "$title" )
quality_label=$(jq -r '.quality_label?' <<< "$json_info") &&
  convert_args+=( -gravity northeast -annotate +0+0 "$quality_label" )
duration_label=$(jq -r ".duration_label?" <<< "$json_info") &&
  convert_args+=( -gravity southwest -annotate +0+0 "$duration_label" )
file_size_label=$(jq -r ".size_label?" <<< "$json_info") &&
  convert_args+=( -gravity southeast -annotate +0+0 "$file_size_label" )

if ! [[ $seconds_between ]]; then
  [[ $duration ]] && seconds_between=$(awk "BEGIN {print ${duration-900} / 31}")
fi
if $FFMPEG -skip_frame nokey -an -vsync 0 -y "${ffmpeg_args[@]}" \
  -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,${seconds_between-30})',tile=${layout}" \
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
  if type wrjpgcom &> /dev/null; then
    wrjpgcom -comment "$json_info" < "$output" > t
	[[ -s t ]] && mv t "$output"
  fi
fi
