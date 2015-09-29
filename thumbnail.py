#!/usr/bin/env python3
import os, os.path
import tempfile
#import time

import tqdm

from . import *

debug("Loading modules")
from .FFmpeg import thumbnails
from .ImageMagick import montage

def thumbnail(input_filename, count, output_filename='{filepart}-{size}-screens.JPG', title='{basename} - {size:,} B', overwrite=False, **kwargs):
	"""Screencap generator for video files.

	input:  required and assumed to be readable as a video file
	count:  total number of thumbnail images
	output:  generalized from input if not given. Substitutions are made for {dirname}, {basename}, {size}, and {ext}
	title:  text appearing on the thumbnail sheet. Substitutions are also made

	overwrite

	Other arguments are passed to the montage() method
	"""
	assert 0 < count

	dirname, basename = os.path.split(input_filename)
	filepart, ext = os.path.splitext(basename)
	size = os.path.getsize(input_filename)
	try:
		output_filename = os.path.join(dirname, output_filename.format(**locals()) )
	except:
		pass
	if os.path.exists(output_filename):
		if overwrite:
			debug("Writing to {output_filename} (exists)".format(**locals()) )
		else:
			warning("Refusing to overwrite '{}'".format(output_filename))
			return None
	else:
		debug("Writing to {output_filename}".format(**locals()))
	try:
		title = title.format(**locals())
	except:
		pass
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
	u = ext.upper()
	if u in [ '.AVI', '.DIVX', '.FLV', '.MPG', '.MPEG', '.MP4', '.MKV', '.MOV', '.WEBM' ]:
		return True
	elif u in [ '.ASF', '.WMV' ]:
		return True
	elif u in [ '.JPG', '.JPEG', '.PNG' ]:
		return False
	elif 8E6 < os.path.getsize(fp):
		warning("Ignoring '{}'".format(fp))
	return False
#
def recurse(*args, video_detector=is_video_file, **kwargs):
	"""Walk through directories generating thumbnails along the way.

	args:	iterable of paths
	video_detector:	emits a truth value to filter on video files

	Other arguments passed to the thumbnail() method:
	overwrite:	by default, existing thumbnails are NOT overwritten
	"""
	options = dict(kwargs)
	debug("Options:")
	for k, v in options.items():
		debug("\t{k}: {v}".format(**locals()))
	video_files = set()
	for arg in args:
		if os.path.isfile(arg):
			video_files += arg
		elif os.path.isdir(arg):
			for root, dirs, files in os.walk(arg):
				dirs = [ d for d in dirs if not d.startswith('.') ]
				files = [ f for f in files if not f.startswith('.') ]
				fps = [ os.path.join(root, f) for f in files ]
				video_files.update(fp for fp in fps if video_detector(fp))
		else:
			error("Ignoring argument '{}'".format(arg))
	for fp in tqdm.tqdm(video_files, desc="Generating frames"):
		yield fp, thumbnail(fp, **options)
