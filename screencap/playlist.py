#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from .m3u import M3U
from .ffprobe import get_info
from .ffmpeg import make_tiles


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def parse_playlist(*args):
    """
    Processes a M3U playlist, injecting values for title and duration for each entry.
    """
    playlist = M3U(*args)
    new_entries = [ ]
    for e in playlist:
        if all(e.get(n) for n in 'duration title'.split()):
            continue
        m = get_info(e['path']) or {}
        m.update(e)
        new_entries.append(m)
    playlist.entries = new_entries
    return playlist


def screencap_playlist(*args, **kwargs):
    pl = parse_playlist(*args, **kwargs)
    if not pl:
        warning("Empty playlist")
    if __debug__:
        for e in pl:
            debug("%s (%s): %s", e['title'], e['path'], sorted(e))
        for line in pl.get_lines():
            debug(line)
    for e in pl:
        if not make_tiles( input_path=e['path'] \
                         , media_info=e \
                         , output_filename=clean_filename(e['filename'])+'_screens.jpeg'):
            error("Screencaps for '%s' failed", e['path'])
