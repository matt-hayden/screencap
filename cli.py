#!/usr/bin/env python3
import os, os.path

from . import *

def main(*args, **kwargs):
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
	results = list(recurse(*args, **options) )
	return all(tfn and os.path.exists(tfn) for vfn, tfn in results)
