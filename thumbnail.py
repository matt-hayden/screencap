#!/usr/bin/env python3
import os, os.path

from FFMpeg import *
from ImageMagick import montage

def thumbnail(input_filename, count=56, **kwinput_filenames):
	dirname, basename = os.path.split(input_filename)
	title, _ = os.path.splitext(basename)
	fs = list(thumbnails(input_filename))
	n = len(fs)
	if n < count:
		selection = fs
	else:
		selection = fs[::n//count]
		while count < len(selection):
			selection.pop(len(selection)//2)
	montage(selection, output_file=basename+'_montage'+'.jpg', title=title, **kwinput_filenames)
if __name__ == '__main__':
	import sys
	myoptions = { 'tile': '8x', 'geometry': '+0+0', 'border': 1,
				  'background': 'transparent', 'bordercolor': 'transparent', 'fill': 'white', 'stroke': 'gray' }
	for arg in sys.argv[1:]:
		print("Generating thumbnails for", arg)
		thumbnail(arg, **myoptions)
