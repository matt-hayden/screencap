#! /bin/bash
: ${FFMPEG=ffmpeg} ${FFPROBE=ffprobe}
set -e

SCRIPT=$(basename ${BASH_SOURCE[0]})

: ${log=`mktemp`} ${errors=`mktemp`}


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


mode=0
while getopts ":hfno:qv0123456789 -:" OPT
do
	if [[ $OPT == '-' ]] # Long option
	then
		OPT=$OPTARG
		eval $OPT && continue || usage # you may or may not want the continue
	fi
	case $OPT in
		-) # long argument, ignore ${OPTARG}
		;;
		h|help) help
		;;
		f|overwrite) overwrite=1
		;;
		o|output) out="$OPTARG"
		;;
		q|quiet) quiet=1
		;;
		[0-9]) mode=$OPT
		;;
		\?) usage # unrecognized options would cause bash error
		;;
	esac
done >&2
shift $((OPTIND-1))

output_options="-show_entries tags=lavfi.black_start,lavfi.black_end,lavfi.scene_score -of flat"
case $mode in
	0)
		function blackdetect() {
			file_in="$1"
			$FFPROBE -f lavfi "movie=${file_in},blackdetect=[out0]" $output_options
		}
	;;
	1|2|3)
		function blackdetect() {
			file_in="$1"
			$FFPROBE -f lavfi "movie=${file_in},blackdetect=d=1[out0]" $output_options
		}
	;;
	4|5|6)
		function blackdetect() {
			file_in="$1"
			$FFPROBE -f lavfi "movie=${file_in},blackdetect=d=1/15[out0]" $output_options
		}
	;;
	7|8|9)
		function blackdetect() {
			file_in="$1"
			$FFPROBE -f lavfi "movie=${file_in},blackdetect=d=1/30:picture_black_ratio_th=0.75:pixel_black_th=0.50[out0]" $output_options
		}
	;;
esac

file_in="$1"
shift
[[ $out ]] || out="${file_in##*/}.blackdetect"
#[[ -e "$out" ]] && ! $((overwrite)) || die "Refusing to overwrite $out"
[[ "$@" ]] && usage

if blackdetect "$file_in" 2>"$errors" | pv -l >"$log"
then
	if [[ -s "$log" ]]
	then
		if mv -b "$log" "$out"
		then
			$((quiet)) || echo "$file_in => $out"
		fi
		exit 0
	fi
else
	cat "$errors" >&2
fi
exit 1
