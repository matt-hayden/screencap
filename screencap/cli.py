#!/usr/bin/env python3
"""Generate contact sheets for video files
  Usage:
    Screencap [options] [--] [PATHS]...

  Options:
    -h --help  show this help message and exit
    --version  show version and exit
    -f, --overwrite  Overwrite existing images
    -j, --join  Don't generate separate images for each file
    -q, --quality=STRING  JPEG compression [default: 35]
    --border=STRING  Border width [default: 1]
    --geometry=STRING  Geometry (see ImageMagick) [default: +0+0]
    --columns=INT  Number of columns [default: 8]
    --rows=INT  Number of rows [default: 7]

"""
import os, os.path


try:
	from . import debug, info, warning, error, fatal
except:
	debug = info = warning = error = fatal = print


def main(*args, **kwargs):
	debug("Arguments:")
	for k, v in kwargs.items():
		debug('\t{}={}'.format(k, v))
	columns = int(kwargs.pop('--columns'))
	options = {
		'border': kwargs.pop('--border'),
		'count': int(kwargs.pop('--rows'))*columns,
		'geometry': kwargs.pop('--geometry'),
		'overwrite': kwargs.pop('--overwrite'),
		'quality': kwargs.pop('--quality'),
		'tile': '{}x'.format(columns)
		}
	if kwargs:
		debug("Unused arguments:")
		for k, v in kwargs.items():
			debug("\t{}={}".format(k, v))
	if kwargs.pop('--join'):
		if all(os.path.isfile(f) for f in args):
			info("Joining files {}".format(args))
			return not thumbdir(args, **options)
		elif all(os.path.isdir(f) for f in args):
			info("Each directory {} will have a joined image".format(args))
			return_val = 0
			for arg in args:
				try:
					thumbdir(arg, **options)
				except Exception as e:
					error("{arg}: {e}".format(**locals()) )
					return_val += 1
			return return_val
		else:
			error("{} is a mix of files and directories, too confused")
			return -1
	else:
		results = list(recurse(*args, **options))
		if not results:
			return 9
		skipped = 0
		for vfn, tfn in results:
			if not tfn:
				info("{} skipped".format(vfn))
				skipped += 1
		if skipped:
			warning("{}/{} skipped".format(skipped, len(results)))
			return 10


if __name__ == '__main__':
	import sys

	import docopt

	kwargs = docopt.docopt(__doc__, version='1.0.2.dev1') # make sure to pop 'PATHS' out as file arguments
	args = kwargs.pop('PATHS') or ['.']
	sys.exit(main(*args, **kwargs))
