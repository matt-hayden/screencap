#! /usr/bin/env bash 
set -e
: ${FFPROBE=ffprobe} ${PV=pv -l -N frames}

type ionice &> /dev/null && FFPROBE="ionice -n 7 $FFPROBE"
[[ -t 2 ]] && FFPROBE="${FFPROBE} -loglevel warning"


mkdir -p "$HOME/.cache/key_frames"
input_path="$@"
[[ -s "$input_path" ]] || echo "'$input_path' not found!" >&2
if [[ -t 0 ]]
then
  json_info=$($FFPROBE -select_streams v -show_streams -print_format json "$input_path")
else
  json_info=$(jq -c .) # capture stdin
fi
nframes=$(jq '[ .streams[] | select(.codec_type=="video") | .nb_frames | tonumber ] | max' <<< "$json_info") && PV="${PV} -s $nframes"

filename="${input_path##*/}"
for outfile in \
	"${input_path}.key_frames" \
	"${filename}.key_frames" \
	"$HOME/.cache/key_frames/${nframes}-${filename}.key_frames"
do
  [[ -s "$outfile" ]] && break
done
if [[ ! -s "$outfile" ]]
then
  $FFPROBE -select_streams v -show_frames \
    -show_entries frame=key_frame,best_effort_timestamp_time \
    -print_format csv "$input_path" |
  $PV |
  awk -F, 'BEGIN { nframes=0 } ($1=="frame") { nframes++ } $2 { print nframes, $3 }' > "$outfile"
fi
if [[ -s "$outfile" ]]
then
	echo "$outfile"
else
	echo "'$input_path' failed!" >&2
fi
