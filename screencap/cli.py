#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import os.path
import sys

from .ffmpeg import make_tiles
from .playlist import screencap_playlist

def main():
    execname, *args = sys.argv
    for arg in args:
        _, ext = os.path.splitext(arg)
        if ext.lower in '.m3u .m3u8'.split():
            screencap_playlist(arg)
        else:
            make_tiles(arg)

