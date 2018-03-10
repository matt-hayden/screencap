#! /usr/bin/env python3
import logging
if __debug__:
    logging.basicConfig(level=logging.DEBUG)

import sys

from . import *
from .util import *


def make_screencaps(verbose=__debug__, playlist_extensions='.m3u .m3u8'.split()):
    """
    Hello
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        _, ext = splitext(arg)
        if ext.lower() in playlist_extensions:
            screencap_playlist(arg)
        else:
            for line in screencap(arg):
                print(line)


def make_split_script(verbose=__debug__):
    """
    Hello
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        for splitter in get_splitter(arg):
            print(splitter.to_script())
            print()


def video_quality_key(e):
    status = e.get('status', (None, None))
    return (not status[1]), -e.get('width', 0), -e.get('bit_rate', 0)
def sort_playlist(verbose=__debug__, key=video_quality_key):
    """
    Hello
    """
    assert callable(key)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        pl = parse_playlist(arg)
        pl.sort(key=key)
        for line in pl.to_m3u(verbose=verbose):
            print(line)
