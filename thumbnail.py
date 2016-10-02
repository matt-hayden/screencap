#!/usr/bin/env python3
import os, os.path
import tempfile
#import time

import tqdm

from . import *

debug("Loading modules")
from .FFmpeg import thumbnails
from .ImageMagick import montage

class ThumbnailError(Exception):
	pass


def is_video_file(path, minimum_size=8E6):
	if path and isinstance(path, str):
		filepart, ext = os.path.splitext(path)
		if filepart.startswith('.'):
			return False
		u = ext.upper()
		if u in [ '.AVI', '.DIVX', '.FLV', '.MPG', '.MPEG', '.MP4', '.MKV', '.MOV', '.WEBM' ]:
			return True
		elif u in [ '.ASF', '.WMV' ]:
			return True
		elif u in [ '.JPG', '.JPEG', '.PNG' ]:
			return False
		elif minimum_size < os.path.getsize(path):
			warning("Ignoring '{}'".format(path))


def thumbdir(root, count, output_filename='{label}-{size}-screens.JPG', title='{label} ~ {nfiles} files ~ {size:,} B', label=None, overwrite=False, video_detector=is_video_file, **kwargs):
	"""Screencap generator for video files.

	input:  required and assumed to be readable as a video file
	count:  total number of thumbnail images
	output:  generalized from input if not given. Substitutions are made for {dirname}, {basename}, {size}, and {ext}
	title:  text appearing on the thumbnail sheet. Substitutions are also made

	overwrite

	Other arguments are passed to the montage() method
	"""
	assert 0 < count
	if isinstance(root, (tuple, list)):
		files = sorted(f for f in root if video_detector(f))
	elif os.path.isdir(root):
		output_filename = os.path.join(root, output_filename)
		files = [ os.path.join(root, f) for f in os.listdir(root) ]
		files = sorted(f for f in files if video_detector(f))
	else:
		raise ThumbnailError("{root} is not a directory or list of filenames")
	label = label or "thumbnail"
	assert files

	size, nfiles = sum(os.path.getsize(f) for f in files), len(files)
	try:
		output_filename = output_filename.format(**locals())
	except:
		warning("Using output '{}', which is not likely what you want".format(output_filename) )
	if os.path.exists(output_filename):
		if overwrite:
			debug("Writing to {} (exists)".format(output_filename))
		else:
			warning("Refusing to overwrite '{}'".format(output_filename))
			return
	else:
		debug("Writing to {}".format(output_filename))
	try:
		title = title.format(**locals())
	except:
		warning("Using title '{}', which is not likely what you want".format(title) )
	with tempfile.TemporaryDirectory() as td:
		fs = []
		for n, fn in enumerate(files):
			info(fn)
			frames_out = list(thumbnails(fn, output_file_pattern=os.path.join(td, '{:08d}-'.format(n)+'%08d.PNG')) )
			if frames_out:
				debug("produced {} frames".format(len(frames_out)) )
				fs.extend(frames_out)
			else:
				error("'{}' ignored".format(fn) )
		assert fs
		n = len(fs)
		if n < count:
			info("thumbdir() produced only {n} frames".format(**locals()) )
			selection = fs
		else:
			debug("thumbdir() produced {n} frames".format(**locals()) )
			debug("Using only {:3.0%}, excluding {}".format(float(count)/n, n-count))
			selection = fs[::n//count]
			while count < len(selection):
				selection.pop(count//2)
		return montage(selection,
					   output_filename=output_filename,
					   title=title,
					   **kwargs)
#
def thumbnail(input_filename, **kwargs):
	dirname, basename = os.path.split(input_filename)
	label, _ = os.path.splitext(basename)
	return thumbdir([input_filename],
					output_filename=os.path.join(dirname, '{label}-{size}-screens.JPG'),
					title='{label} ~ {size:,} B',
					label=label,
					**kwargs)
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
			video_files.add(arg)
		elif os.path.isdir(arg):
			for root, dirs, files in os.walk(arg):
				dirs = [ d for d in dirs if not d.startswith('.') ]
				files = [ f for f in files if not f.startswith('.') ]
				fps = [ os.path.join(root, f) for f in files ]
				video_files.update(fp for fp in fps if video_detector(fp))
		else:
			error("Ignoring argument '{}'".format(arg))
	for fp in tqdm.tqdm(video_files):
		try:
			yield fp, thumbnail(fp, **options)
		except Exception as e:
			error("{fp} failed: {e}".format(**locals()))
