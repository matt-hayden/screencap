#!/usr/bin/env python3
import sys

from .thumbnail import recurse

myoptions = { 'tile': '8x', 'geometry': '+0+0', 'border': '1', 'quality': '35' }
for src, ss in recurse(sys.argv[1:], **myoptions):
	if ss:
		print(src, "->", ss)
