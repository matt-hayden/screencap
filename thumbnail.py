#!/usr/bin/env python3
from FFMpeg import *

import sys
for arg in sys.argv[1:]:
	thumbnails(arg)
	thumbnail_mosaic(arg)
