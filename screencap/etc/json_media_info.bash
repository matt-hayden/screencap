#! /usr/bin/env bash
FFPROBE=ffprobe
[[ -t 2 ]] && FFPROBE="$FFPROBE -loglevel warning"

function to_object() {
  jq "{ \"$*\": . }"
}
export -f to_object

parallel "$FFPROBE -show_format -show_streams -show_chapters -show_data_hash SHA256 -print_format json {} | to_object {}" ::: "$@" | jq -s 'add'
