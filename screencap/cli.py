#! /usr/bin/env python3
import logging
import os.path
import sys

from .ffmpeg import make_tiles
from .playlist import screencap_playlist


def splitext(text):
    parts = text.rsplit('.', 1)
    if (1 == len(parts)):
        return parts.pop(), ''
    return parts[0], '.'+parts[1]


def main(verbose=__debug__, playlist_extensions='.m3u .m3u8'.split()):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        _, ext = splitext(arg)
        if ext.lower() in playlist_extensions:
            screencap_playlist(arg)
        else:
            make_tiles(arg)

