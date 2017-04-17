#! /bin/bash
: ${FFMPEG=ffmpeg} ${MPLAYER=mplayer}

set -e

SCRIPT=$(basename ${BASH_SOURCE[0]})

function help() {
	cat <<- EOF
This is help
EOF
	caller 0
	exit -1
}

function usage() {
	cat <<- EOF
This is usage
EOF
	caller 0
	exit -1
}

function die() {
	echo <<< "$@"
	exit -1
}

mode=5
while getopts ":hd:f:0123456789 -:" OPT
do
	if [[ $OPT == '-' ]] # Long option
	then
		OPT=$OPTARG
		eval $OPT && continue || usage # you may or may not want the continue
	fi
	case $OPT in
		-) echo Long option: $OPT $OPTARG # the continue above prevents reaching this
		;;
		h|help) help
		;;
		d|dest) dest="$OPTARG"
		;;
		f|format) format="$OPTARG"
		;;
		[0-9]) mode=$OPT
		;;
		\?) usage # getopts replaces unknown with ?
		;;
	esac
done >&2
shift $((OPTIND-1))

## defaults
format=png # jpeg
##

ext="${format##.}"

file_in="$1"
[[ -f "$file_in" ]] || die "file $file_in not found"
shift
[[ "$@" ]] && usage
basename="${file_in##*/}"
filepart="${basename%.*}"
[[ $dest ]] || dest="${basename}_thumbs"
mkdir -p "$dest"
[[ $errors ]] || errors="$dest/errors"

case $mode in
	0|1|2)
		function thumbs() {
			file_in="$1"
			out="${dest}/${filepart}_%08d${ext}"
			$FFMPEG -an -nostdin -i "$file_in" -f image2 -vframes 1 -vsync drop "$out"
		}
	;;
	3|4)
		function thumbs() {
			file_in="$1"
			out="${dest}/${filepart}_%08d${ext}"
			$FFMPEG -an -nostdin -i "$file_in" -f image2 -vf 'fps=1/240' -vsync drop "$out"
		}
	;;
	5|6)
		function thumbs() {
			file_in="$1"
			out="${dest}/${filepart}_%08d${ext}"
			$FFMPEG -an -nostdin -i "$file_in" -f image2 -vf select='eq(pict_type\,PICT_TYPE_I)' -vsync drop "$out"
		}
	;;
	7|8|9)
		function thumbs() {
			file_in="$1"
			out="${format}:${dest}"
			$MPLAYER -nosound -ss 240 "$file_in" -frames 64 -vo "$out"
		}
	;;
esac

if thumbs "$file_in" &> "$errors"
then
	echo "$dest"
	exit 0
else
	cat "$errors" >&2
fi
exit 1
