#! /usr/bin/env bash
: ${FFPROBE=ffprobe}

[[ -t 2 ]] && FFPROBE="${FFPROBE} -loglevel warning"
exec $FFPROBE "$@"
