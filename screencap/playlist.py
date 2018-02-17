#! /usr/bin/env python3
import multiprocessing
logger = multiprocessing.get_logger() # does not accept 'name' argument
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
from datetime import datetime
import itertools
import os.path
import urllib.parse

import requests

from .ffmpeg import make_tiles
from . import ffprobe
from .m3u import M3U
from .util import *

now = datetime.now


RequestException = requests.exceptions.RequestException


class Cache(collections.OrderedDict):
    def resize(self, newsize):
        for _ in range(len(self)-newsize):
            self.popitem(last=False)


def _parse_entries(host_entries, required_members='duration title'.split(), skip_root=False):
    """
    Worker for parse_playlist()
    """
    cache = Cache()
    def get_info(*args, **kwargs):
        r = cache[args] = cache.get(args, None) or ffprobe.get_info(*args, **kwargs) or {}
        return dict(r) # return a copy

    host, entries = host_entries
    if host:
        debug("host '%s': %d paths", host, len(entries))
    else:
        debug("%d local paths", len(entries))
    results = []
    y = results.append
    if host:
        with requests.Session() as s:
            ### Check if the host is up
            if not skip_root:
                ok = None
                try:
                    ok = s.head('http://%s/' % host).ok
                except RequestException:
                    ok = False
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
                except RequestException:
                    ok = False
                e['status'] = (now(), ok)
                if ok:
                    m = get_info(url)
                    if m:
                        y({**m, **e})
                        continue
                y(e)
    else:
        for e in entries:
            path = e['path']
            ok = os.path.exists(path)
            if ok:
                m = get_info(path)
                if m:
                    y({**m, **e})
                    continue
            else:
                warn("'%s' not found", path)
            y(e)
    debug("cached %d calls to host '%s'", len(cache), host or '(none)')
    return results


def parse_playlist(*args):
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
    with multiprocessing.Pool( min(len(host_entries), 32) ) as pool:
        for level in pool.imap_unordered(_parse_entries, host_entries.items()):
            for e in level:
                assert e
                new_entries[e['order']] = e
    assert None not in new_entries
    playlist.entries = new_entries
    return playlist


def screencap_playlist(*args, **kwargs):
    pl = parse_playlist(*args, **kwargs)
    if not pl:
        warning("Empty playlist")
        return
    for filename, entries in itertools.groupby(pl, lambda e: e['filename']):
        entries = list(entries)
        if (1 < len(entries)):
            def namer(e, n):
                t = e.get('title', None)
                if t:
                    return clean_filename(t)+'_screens.jpeg'
                return '%s_Scene-%03d_screens.jpeg' % (clean_filename(filename), n)
        else:
            namer = lambda e, n: clean_filename(filename)+'_screens.jpeg'
        for n, e in enumerate(entries):
            if not make_tiles(input_path=e['path'], output_filename=namer(e, n), **e):
                error("Screencaps for '%s' failed", e)
        info("%d images created for '%s'" % (n, filename))
