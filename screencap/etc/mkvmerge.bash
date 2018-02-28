#! /usr/bin/env bash
: ${MKVMERGE=mkvmerge}
type ionice &> /dev/null && MKVMERGE="ionice -n 7 $MKVMERGE"

[[ -t 2 ]] && MKVMERGE="${MKVMERGE} -q"
exec $MKVMERGE "$@"
