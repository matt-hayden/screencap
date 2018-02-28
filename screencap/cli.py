#! /usr/bin/env python3
import logging
import os.path
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
            make_tiles(arg)


def make_split_script(verbose=__debug__):
    """
    Hello
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        for splitter, splitter_args in get_splitter(arg):
            print(splitter.to_script(splitter_args))


def video_quality_key(e):
    return -e.get('width', 0), -e.get('bit_rate', 0)
def sort_playlist(verbose=__debug__, key=video_quality_key):
    """
    Hello
    """
    assert callable(key)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    contents = []
    for arg in args:
        with open(arg, 'Ur') as fi:
            lines = filter(None, (line.strip() for line in fi))
            contents.extend(lines)
    pl = parse_playlist(contents)
    pl.sort(key=key)
    for line in pl.get_lines(verbose=verbose):
        print(line)
