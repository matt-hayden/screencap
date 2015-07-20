#!/usr/bin/env python3
import os, os.path
import tempfile

from FFMpeg import *
from ImageMagick import montage

def thumbnail(input_filename, output_filename=None, count=56, **kwargs):
	dirname, basename = os.path.split(input_filename)
	filepart, _ = os.path.splitext(basename)
	size = os.path.getsize(input_filename)
	if not output_filename:
		output_filename = os.path.join(dirname, "{}-{}-screens.JPG".format(filepart, size))
	title = "{} - {:,} B".format(basename, size)
	fs = list(thumbnails(input_filename, output_file_pattern=os.path.join(tempfile.mkdtemp(), '%08d.PNG')) )
	n = len(fs)
	if n < count:
		selection = fs
	else:
		selection = fs[::n//count]
		while count < len(selection):
			selection.pop(len(selection)//2)
	montage(selection, output_filename=output_filename, title=title, **kwargs)
if __name__ == '__main__':
	import sys
	myoptions = { 'tile': '8x', 'geometry': '+0+0', 'border': 1, 'quality': '35' }
	for arg in sys.argv[1:]:
		print("Generating thumbnails for", arg)
		thumbnail(arg, **myoptions)
