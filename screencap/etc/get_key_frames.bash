#! /usr/bin/env bash
set -e
: ${FFPROBE=ffprobe} ${PV=pv}

[[ -t 2 ]] && FFPROBE="${FFPROBE} -loglevel warning"

function get_nframes() {
  $FFPROBE -select_streams v -show_streams -print_format json "$@" |
  jq '[ .streams | .[].nb_frames | tonumber ] | max'
}

while getopts ":n:q" flag
do
  case "${flag}" in
    n) nframes="$OPTARG" ;;
    q) quiet=1 ;;
    :)
      echo "Option -$OPTARG requires an argument."
      exit 1
      ;;
    \?) # Error condition is literal '?'
      cat <<-EOF
Usage: get_key_frames
  -n nframes  Override automatic detection of number of frames
  -q    No output

EOF
      exit 1
      ;;
    *) # Should not occur
      echo "Unknown error while processing options"
      ;;
  esac
done >&2
shift $((OPTIND-1))

(( quiet )) && FFPROBE="${FFPROBE} -loglevel error"

mkdir -p "$HOME/.cache/key_frames"
filepath="$@"
filename="${filepath##*/}"
if [[ $nframes ]] || nframes=$(get_nframes "$filepath")
then
  PV="${PV} -s $nframes"
fi
for outfile in "${filepath}.key_frames" "${filename}.key_frames" "$HOME/.cache/key_frames/${nframes}-${filename}.key_frames"
do
  [[ -s "$outfile" ]] && break
done
if [[ ! -s "$outfile" ]]
then
  $FFPROBE -select_streams v -show_frames \
    -show_entries frame=key_frame,best_effort_timestamp_time \
    -print_format csv "$filepath" |
  $PV -l -N "video frames" |
  awk -F, 'BEGIN { nframes=0 } ($1=="frame") { nframes++ } $2 { print nframes, $3 }' > "$outfile"
fi
[[ -s "$outfile" ]] && echo "$outfile" || echo "$filepath failed!" >&2
