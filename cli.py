#!/usr/bin/env python3
import os, os.path

from . import *

def main(*args, **kwargs):
	options = {
		'border': kwargs.pop('--border'),
		'count': int(kwargs.pop('--rows'))*int(kwargs['--columns']),
		'geometry': kwargs.pop('--geometry'),
		'overwrite': kwargs.pop('--overwrite'),
		'quality': kwargs.pop('--quality'),
		'tile': '{}x'.format(kwargs.pop('--columns'))
		}
	if kwargs:
		debug("Unused arguments:")
		for k, v in kwargs.items():
			debug("{}={}".format(k, v))
	dirs = [ p for p in args if os.path.isdir(p) ]
	files = set(args) - set(dirs)
	for src in files:
		ss = thumbnail(src, **options)
		if ss:
			info("‘{}’ -> ‘{}’".format(src, ss))
	for src, ss in recurse(dirs, **options):
		if ss:
			info("‘{}’ -> ‘{}’".format(src, ss))
