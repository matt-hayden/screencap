#! /usr/bin/env bash
: ${FFMPEG=ffmpeg}

type ionice &> /dev/null && FFMPEG="ionice -n 7 $FFMPEG"

[[ -t 0 ]] || FFMPEG="${FFMPEG} -nostdin"
[[ -t 2 ]] && FFMPEG="${FFMPEG} -loglevel warning"
exec $FFMPEG "$@"
