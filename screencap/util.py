#! /usr/bin/env python3
# intended to 'from .util import *'
import collections
from datetime import timedelta
import os, os.path
from pathlib import Path


module_path, _ = os.path.split(__file__)
etc_path = Path(module_path) / 'etc'


class Cache(collections.OrderedDict):
    def resize(self, newsize):
        for _ in range(len(self)-newsize):
            self.popitem(last=False)


def pathsplit(text):
    p = text.rsplit('/', 1)
    if len(p) == 1:
        return '', p[0]
    return p


def splitext(text):
    p = text.rsplit('.', 1)
    if len(p) == 1:
        return p[0], ''
    return p[0], '.'+p[-1]


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


def pop_start_stop_duration(media_info):
    """
    media_info is a dict, and will be modified in-place

    duration is expected to represent total file duration, not subject to the start and stop times.
    """
    start = media_info.pop('start-time', 0.)
    stop = media_info.pop('stop-time', None)
    if 'duration' in media_info:
        duration = media_info.pop('duration')
        if isinstance(duration, timedelta):
            duration = duration.total_seconds()
        else:
            duration = float(duration)
    else:
        duration = None
    file_duration = duration
    if stop:
        duration = stop
    if start:
        duration -= start
    assert duration
    assert 0 <= duration, "Could not determine file duration"
    return ((start, stop), (duration, file_duration))
