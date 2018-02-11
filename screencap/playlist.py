#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import sys

from .m3u import M3U
from .ffprobe import get_info
from .ffmpeg import make_tiles


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def parse_playlist(playlist_filename):
    """
    Processes a M3U playlist, injecting values for title and duration for each entry.
    """
    playlist = M3U(playlist_filename)
    for e in playlist:
        url = e['url']
        filename = e['filename']
        media_info = None
        title = e.get('title', None)
        if not title:
            tags = e['m3u_meta']['tags']
            if tags:
                title = e['title'] = tags.pop(0)
        if not title:
            media_info = media_info or get_info(url) or {}
            title = e['title'] = media_info.pop('title', None)
        if not title:
            title = e['title'] = filename.rsplit('.', 1)[0]
        duration = e.get('duration', None)
        if not duration:
            media_info = media_info or get_info(url) or {}
            duration = e['duration'] = media_info.pop('duration', None)
        if not duration:
            duration = e['direction'] = e['m3u_meta'].pop('duration', None)
        e['ffprobe_meta'] = media_info
    return playlist


def screencap_playlist(*args, **kwargs):
    for e in parse_playlist(*args, **kwargs):
        url = e['url']
        if not make_tiles( url \
                         , duration=e['duration'] \
                         , output_filename=clean_filename(e['filename'])+'_screens.jpeg'):
            error("Screencaps for '%s' failed", url)
