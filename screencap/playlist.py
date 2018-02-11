#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import sys

from .m3u import M3U
from .ffmpeg import make_tiles


def clean_filename(text, dropchars='/'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def screencap_playlist(playlist_filename):
    playlist = M3U(playlist_filename)
    for e in playlist:
        uri = e['uri']
        filename = uri.rsplit('/', 1)[-1]
        title = e.get('title', None)
        if not title:
            tags = e['m3u_meta']['tags']
            if tags:
                title = e['title'] = tags.pop(0)
            else:
                title = e['title'] = filename
        duration = e.get('duration', None)
        if not duration:
            duration = e['direction'] = e['m3u_meta'].pop('duration', None)
        if not make_tiles(uri, duration=duration, output_filename=clean_filename(title)+'_screens.jpeg'):
            error("Screencaps for '%s' failed", uri)
