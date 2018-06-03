#! /usr/bin/env python3
import logging
if __debug__:
    logging.basicConfig(level=logging.DEBUG)

from datetime import timedelta
import os, os.path
import sys

import json

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


def insert_screencap_defaults(verbose=__debug__):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    md = json.load(sys.stdin)
    if 'title' not in md:
        try:
            md['title'] = md['format']['tags']['title']
        except KeyError:
            pass
    if not md.get('title', None):
        md['title'], _ = os.path.splitext(md['format']['filename'])
    if 'duration_label' not in md:
        d = timedelta(seconds=float(md['format']['duration']))
        md['duration_label'] = str(d).strip(' :0')
    if 'quality_label' not in md:
        mbit_rate = int(md['format']['bit_rate'])/1E6
        vts = [ s for s in md['streams'] if s['codec_type'] == 'video' ]
        mpixels = max(s.get('width', 0)*s.get('height', 0) for s in vts)/1E6
        md['quality_label'] = '%0.1f Mpx @ %0.1f Mbit' %(mpixels, mbit_rate)
    if 'size_label' not in md:
        md['size_label'] = '{:,d} bytes'.format(int(md['format']['size']))
    print(json.dumps(md, indent=2))
