#! /usr/bin/env python3

from datetime import timedelta


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
        duration = float(media_info.pop('duration'))
    else:
        duration = None
    if stop:
        duration = stop
    if start:
        duration -= start
    assert duration
    if isinstance(duration, timedelta):
        duration, duration_timestamp = duration.total_seconds(), duration
    else:
        duration_timestamp = timedelta(seconds=duration)
    assert 0 <= duration, "Could not determine file duration"
    return ((start, stop), (duration_timestamp, duration))
