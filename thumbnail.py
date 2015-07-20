#!/usr/bin/env python3
import os, os.path
import tempfile

from FFMpeg import *
from ImageMagick import montage

def thumbnail(input_filename, output_filename=None, count=56, overwrite=True, **kwargs):
	"""Screencap generator for video files.

	input:	required and assumed to be readable as a video file
	output:	generalized from input if not given. The format is existing_filename-size-screens.ext
	count:	total number of thumbnails to display
	overwrite:	by default, existing screens are overwritten

	Other arguments are passed to the montage() method
	"""
	dirname, basename = os.path.split(input_filename)
	filepart, _ = os.path.splitext(basename)
	size = os.path.getsize(input_filename)
	if not output_filename:
		output_filename = os.path.join(dirname, "{}-{}-screens.JPG".format(filepart, size))
	if not overwrite and os.path.exists(output_filename):
		return None
	title = "{} - {:,} B".format(basename, size)
	with tempfile.TemporaryDirectory() as td:
		fs = list(thumbnails(input_filename, output_file_pattern=os.path.join(td, '%08d.PNG')) )
		n = len(fs)
		if n < count:
			selection = fs
		else:
			selection = fs[::n//count]
			while count < len(selection):
				selection.pop(count//2)
		return montage(selection, output_filename=output_filename, title=title, **kwargs)

def is_video_file(fp):
	_, ext = os.path.splitext(fp)
	if ext.upper() in [ '.AVI', '.DIVX', '.FLV', '.MPG', '.MPEG', '.MP4', '.MKV', '.MOV', '.WEBM' ]:
		return True
	elif ext.upper() in [ '.ASF', '.WMV' ]:
		return True
	elif 8E6 < os.path.getsize(fp):
		print("Ignoring", fp)
	return False
#
def recurse(args, successes=[], failures=[], video_detector=is_video_file, **kwargs):
	"""Walk through directories generating thumbnails along the way.

	args:	iterable of paths
	video_detector:	emits a truth value to filter on video files

	Other arguments passed to the thumbnail() method:
	overwrite:	by default, existing thumbnails are NOT overwritten
	"""
	for arg in args:
		for root, dirs, files in os.walk(arg):
			for fn in files:
				fp = os.path.join(root, fn)
				if video_detector(fp):
					try:
						thumbnail(fp, overwrite=False, **kwargs)
						successes.append(fp)
					except:
						failures.append(fp)
				else:
					print("Ignoring", fp)
	return successes, failures
#
if __name__ == '__main__':
	import sys
	myoptions = { 'tile': '8x', 'geometry': '+0+0', 'border': '1', 'quality': '35' }
	successes, failures = recurse(sys.argv[1:], **myoptions)
	if successes:
		with open('successes.list', 'w') as fo:
			fo.write('\n'.join(successes))
			fo.write('\n')
	if failures:
		with open('failures.list', 'w') as fo:
			fo.write('\n'.join(failures)+'\n')
			fo.write('\n')
