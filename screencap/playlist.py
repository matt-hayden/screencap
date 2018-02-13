#! /usr/bin/env python3
import multiprocessing
logger = multiprocessing.get_logger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import itertools
import urllib.parse

import requests

from .m3u import M3U
from .ffprobe import get_info
from .ffmpeg import make_tiles

ConnectionError = requests.exceptions.ConnectionError
InvalidSchema = requests.exceptions.InvalidSchema


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def _parse_entries(host_entries, required_members='duration title'.split(), skip_root=False):
    """
    Worker for parse_playlist()
    """
    host, entries = host_entries
    results = []
    y = results.append
    if host:
        with requests.Session() as s:
            ### Check if the host is up
            if not skip_root:
                ok = None
                try:
                    ok = s.head('http://%s/' % host).ok
                except ConnectionError:
                    ok = False
                if (ok == False):
                    warn("Host %s is down", host)
                    return entries
            ### March through the entries
            for e in entries:
                url = e['url'].geturl()
                if required_members: # set required_members=None to skip this
                    if all(e.get(_, None) for _ in required_members):
                        debug("Skipping '%s'", url)
                        y(e)
                        continue
                ### Check if the URL is up
                try:
                    ok = s.head(url).ok
                except ConnectionError:
                    ok = False
                except InvalidSchema:
                    ok = 'unknown'
                if ok:
                    e['status'] = ok
                    m = get_info(url)
                    if m:
                        m.update(e)
                        y(m)
                        continue
                y(e)
    else:
        for e in entries:
            m = get_info(e['path'])
            if m:
                m.update(e)
                y(m)
            else:
                y(e)
    return results


def parse_playlist(*args, pool=multiprocessing.Pool()):
    """
    Processes a M3U playlist, injecting values for title and duration for each entry.
    """
    def host_key(e):
        if 'url' in e:
            return e['url'].hostname.lower()
        return ''
    playlist = M3U(*args)
    new_entries = [None]*len(playlist)
    host_entries = { h: list(es) for h, es in itertools.groupby(sorted(playlist.entries, key=host_key), key=host_key) }
    info("Processing %d different hosts for %d entries", len(host_entries), len(playlist))
    debug( ' '.join( (h or '(none)') for h in sorted(host_entries.keys(), key=lambda s: s.lower() if isinstance(s, str) else '') ) )
    for level in pool.imap_unordered(_parse_entries, host_entries.items()):
        for e in level:
            new_entries[e['order']] = e
    playlist.entries = new_entries
    return playlist


def screencap_playlist(*args, **kwargs):
    pl = parse_playlist(*args, **kwargs)
    if not pl:
        warning("Empty playlist")
    if __debug__:
        for e in pl:
            debug(e)
        for line in pl.get_lines():
            debug(line)
    for e in pl:
        if not make_tiles( input_path=e['path'] \
                         , media_info=e \
                         , output_filename=clean_filename(e['filename'])+'_screens.jpeg'):
            error("Screencaps for '%s' failed", e)
