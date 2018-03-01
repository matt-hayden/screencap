#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import itertools
import os, os.path

from . import *

from .ffmpeg import FFMpegSplitter
from .m3u import M3U
from .mkvmerge import MkvMergeSplitter
from .util import *


def get_output_filename(entry):
    if entry.get('title', None):
        return entry['title']+'.MKV'
def get_output_dir(entry):
    tags = entry.get('tags', [])
    if len(tags) == 1:
        od = tags[-1]
        if od and (' ' not in od):
            return od
def get_splitter(*args, \
        default_profiles=[ ('ffmpeg', FFMpegSplitter) ], \
        get_output_filename=get_output_filename, \
        get_output_dir=get_output_dir, \
        **kwargs):
    """
    Generate commands to reduce the on-disk file size of a playlist.

    Yields pairs of:
        (splitter object, arguments)
        The splitter object has members (which you can modify) like:
            execname
            input_path
        Call splitter.to_script(arguments) to flatten into a bash script
    """
    def key(e):
        if 'url' in e:
            return False, e['url'].lower()
        else:
            assert 'path' in e
            return True, e['path']
    assert callable(get_output_filename)
    assert callable(get_output_dir)
    playlist = M3U(*args)
    playlist.sort(key=key)
    for (is_local, path), entries in itertools.groupby(playlist, key=key):
        entries = list(entries)
        profiles = collections.OrderedDict(default_profiles)
        options = dict(kwargs)
        options['input_path'] = path
        if is_local:
            _, filename = os.path.split(path)
            filepart, ext = os.path.splitext(filename)
            if ext.lower() in ['', '.mkv', '.mp4', '.webm']:
                profiles['mkvmerge'] = MkvMergeSplitter
        duration = options.get('duration', None)
        if not duration:
            durations = set( filter(None, (e.get('duration', None) for e in entries)) )
            if len(durations) == 0:
                media_info = get_info(path)
                duration = media_info['duration']
            elif len(durations) == 1:
                duration ,= durations
            else:
                if 1 < len(durations):
                    warn("Multiple values for duration of '%s': %s", path, sorted(durations))
                duration = max(durations)
            options['duration'] = duration
        entries.sort(key=lambda e: (e.get('start-time', 0), e.get('stop-time', duration)) )
        for file_order, entry in enumerate(entries, start=1):
            if 'output_filename' not in entry:
                entry['output_filename'] = \
                        get_output_filename(entry) or '%s-%03d.MKV' % (filepart, file_order)
            if 'output_dir' not in entry:
                od = get_output_dir(entry)
                if od:
                    entry['output_dir'] = od
        for name, splitter in profiles.items():
            pass
        info("Using splitter %s", name)
        yield splitter(entries, **options), entries
