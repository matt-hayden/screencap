#!/usr/bin/env python3
import os, os.path

from .thumbnail import thumbnail, recurse

def run(*args, **kwargs):
	options = kwargs or { 'tile': '8x', 'geometry': '+0+0', 'border': '1', 'quality': '35' }
	dirs = [ p for p in args if os.path.isdir(p) ]
	files = set(args) - set(dirs)
	for src in files:
		ss = thumbnail(src, **options)
		if ss:
			print("‘{}’ -> ‘{}’".format(src, ss))
	for src, ss in recurse(dirs, **options):
		if ss:
			print("‘{}’ -> ‘{}’".format(src, ss))
