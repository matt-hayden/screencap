#! /usr/bin/env python3
import bisect
from decimal import Decimal
import collections
import os, os.path
from pathlib import Path
import subprocess

from .util import *


class FramePair(collections.namedtuple('FramePair', 'frame_number timestamp')):
    pass

class KeyFrames:
    def __init__(self, arg, **kwargs):
        if isinstance(arg, (str, Path)):
            filename = self.filename = arg
            self.load_video(filename)
        else:
            self.rows = arg
    def load_video(self, *args, nframes=None, **kwargs):
        filename, = args
        execname = str(etc_path / 'get_key_frames.bash')
        if nframes:
            args = [ execname, '-n', str(nframes), str(filename) ]
        else:
            args = [ execname, str(filename) ]
        proc = subprocess.run(args, stdout=subprocess.PIPE)
        assert (0 == proc.returncode)
        rows = self.rows = []
        y = rows.append
        for line in proc.stdout.decode().split('\n'):
            if not line.strip():
                continue
            f, t = line.split()
            y( FramePair(int(f), Decimal(t)) )
        rows.sort()
    def find(self, value, direction=-1):
        rows = self.rows
        if isinstance(value, int):
            keys = [ row.frame_number for row in rows ]
            assert (1 <= value), "Frame numbers start at 1"
        elif isinstance(value, Decimal):
            keys = [ row.timestamp for row in rows ]
        elif isinstance(value, str):
            value = Decimal(value)
            keys = [ row.timestamp for row in rows ]
        else:
            raise ValueError("Invalid parameter %s" % value)
        if (-1 == direction): # rightmost less than or equal to arg
            i = bisect.bisect_right(keys, value)
            if i:
                return rows[i-1]
            raise ValueError("No frames before %s" % value)
        elif (1 == direction): # leftmost greater than or equal to
            i = bisect.bisect_left(keys, value)
            if i < len(rows):
                return rows[i]
            raise ValueError("No frames after %s" % value)
        raise ValueError("Invalid parameter %s" % direction)
