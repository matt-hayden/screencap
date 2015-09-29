#!/usr/bin/env python3
import os, os.path
import tempfile
#import time

import tqdm

from . import *

debug("Loading modules")
from .FFmpeg import thumbnails
from .ImageMagick import montage

def thumbnail(input_filename, count, output_filename=None, overwrite=True, **kwargs):
	"""Screencap generator for video files.

	input:	required and assumed to be readable as a video file
	count:	total number of thumbnails to display
	output:	generalized from input if not given. The format is existing_filename-size-screens.ext
	overwrite:	by default, existing screens are overwritten

	Other arguments are passed to the montage() method
	"""
	assert 0 < count
	dirname, basename = os.path.split(input_filename)
	filepart, _ = os.path.splitext(basename)
	size = os.path.getsize(input_filename)
	if not output_filename:
		output_filename = os.path.join(dirname, "{}-{}-screens.JPG".format(filepart, size))
	if not overwrite and os.path.exists(output_filename):
		warning("Refusing to overwrite '{}'".format(output_filename))
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
	options = { 'overwrite': False } # defaults
	options.update(kwargs)
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
