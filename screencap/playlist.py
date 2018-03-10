#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import itertools
import os.path
import urllib.parse

from .ffmpeg import get_screencap_commands
from .ffprobe import get_media_profile, get_media_profiles
from .m3u import *

from .util import *


import requests

RequestException = requests.exceptions.RequestException


def _parse_entries(arg, \
        failures_allowed=10, \
        VLC_custom_EXTINF=True, \
        VLC_custom_folders=True):
    """
    Worker for parse_playlist()

    """
    filename_or_hostname, is_remote, entries = arg
    #results = []
    #y = results.append
    if is_remote: # single host, with possibly multiple input files
        hostname = filename_or_hostname
        with requests.Session() as s:
            ok = None
            try:
                ok = s.head('http://%s/' % hostname).ok
            except RequestException:
                ok = False
                warn("Host %s not reachable", hostname)
                failures_allowed = 1
            if failures_allowed:
                info("Host %s appears up", hostname)
                for e in entries:
                    if not failures_allowed:
                        error("Too many failures on host %s", hostname)
                        break
                    url = e.remote
                    try:
                        ok = s.head(url).ok
                    except RequestException:
                        failures_allowed -= 1
                        ok = False
                    e['status'] = (now(), ok)
                    if ok:
                        e.update_metadata()
                else:
                    info("Done with host %s", hostname)
    else: # single local input file
        path = filename_or_hostname
        filename = path.name
        for e in entries:
            e.update_metadata()
            e['status'] = (now(), path.exists())
    entries.sort(key=file_starttime_key)
    # Generate output names for further processing. These are filename-based.
    for input_path, es in itertools.groupby(entries, key=file_key):
        if isinstance(input_path, Path):
            basename = input_path.name
        else:
            basename = input_path.rsplit('/', 1)[-1]
        filename_pattern, video_ext = os.path.splitext(basename)
        basename = clean_filename(basename)
        if video_ext.lower() in '.avi .divx .flv .mpg'.split():
            info('Converting %s file to MKV', video_ext)
            video_ext = '.MKV'
        else:
            debug('Assuming %s file is convertible', video_ext)
        for n, e in enumerate(es, start=1):
            output_folder = e.playlist.folder
            output_filename = (basename+'_Scene-%03d'+video_ext) % n
            screens_filename = (basename+'_Scene-%03d_screens.jpeg') % n
            if VLC_custom_EXTINF:
                a = e.get('Artist', '')
                if a:
                    output_filename = a+video_ext
                    screens_filename = a+'.jpeg'
                track_name = e._ordered_titles.pop('tagged', '')
                if VLC_custom_folders and (',' not in track_name):
                    output_folder /= Path(track_name)
                elif track_name:
                    e.set_title(track_name)
            if e.get_title() == filename_pattern:
                e.set_title('%s Split %d' % (filename_pattern, n))
            e['output_path'] = output_folder / clean_filename(output_filename)
            e['screens_path'] = output_folder / clean_filename(screens_filename)
    return entries


def parse_playlist(arg, nprocs=None):
    """
    Processes a M3U playlist, injecting values for title and duration for each entry.
    """
    playlist = M3U(arg) # modified in-place
    info("Reading %d entries", len(playlist))
    playlist._precompute_metadata()
    es = []
    for lre in playlist.by_host():
        es.extend(_parse_entries(lre))
    es.sort(key=file_order)
    for e in es:
        debug("Line %d '%s' -> %s", file_order(e), e.remote or e.path, e.keys())
    playlist.entries = es
    return playlist


def screencap_playlist(arg, **kwargs):
    if isinstance(arg, M3U):
        playlist = arg
    else:
        playlist_filename = arg
        playlist = parse_playlist(playlist_filename, **kwargs)
    if not len(playlist):
        warning("Empty playlist")
        return
    failures = 0
    for filename_or_host, is_remote, entries in playlist.by_host():
        for e in entries:
            """
            # Devise some labels for the graphic
            starttime, stoptime = e.get('start-time', None), e.get('stop-time', None)
            dur_s = time_s(e.get_duration())
            if starttime or stoptime:
                starttime = time_s(starttime) or '-'
                stoptime = time_s(stoptime) or dur_s
                dur_s = starttime+'-'+stoptime
            size_s = '%.2f Mpx [%sx%s]' % (e.get('megapixels', 0), \
                    e.get('width', 0), \
                    e.get('height', 0))
            if ('Artist' in e) or ('tags' in e):
                label = ' - '.join( filter(None, [e.get('Artist', None)]+e.get('tags', [])) )
            else:
                label = e.get_title()
            annotation = [ label, size_s, dur_s, \
                    "{:,d} bytes".format(e['file_size']) ]
            # Build the command line
            for line in get_screencap_commands(e.remote or e.path, title=e.get_title(), **e):
                print(line)
                print()
            """
            ###
            command_args = []
            if 'start-time' in e:
                command_args += [ '-ss', e['start-time'] ]
            command_args += [ '-i', e.remote or e.path ]
            if 'stop-time' in e:
                command_args += [ '-to', e['stop-time'] ]
            for line in get_screencap_commands(*command_args, **e.retrieve_metadata()):
                print(line)
            print()
