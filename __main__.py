#!/usr/bin/env python3
"""Generate contact sheets for video files
  Usage:
    Screencap [options] [--] PATHS...

  Options:
    -h --help  show this help message and exit
    --version  show version and exit
    -f, --overwrite  Overwrite existing screencap files
    -q, --quality=STRING  JPEG compression [default: 35]
    --border=STRING  Border width [default: 1]
    --geometry=STRING  Geometry (see ImageMagick) [default: +0+0]
    --columns=INT  Number of columns [default: 8]
    --rows=INT  Number of rows [default: 7]

"""
import sys

import docopt

from . import *
from .cli import main

args = docopt.docopt(__doc__, version=__version__) # make sure to pop 'PATHS' out as file arguments
sys.exit(main(*args.pop('PATHS'), **args))
