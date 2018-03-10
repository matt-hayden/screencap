#! /usr/bin/env python3
"""
Find closest keyframe to a timestamp or frame number in a video.

Relies on bundled script get_key_frames.bash
"""

import bisect
from decimal import Decimal
import collections
import os, os.path
from pathlib import Path
#import subprocess

from .util import *

execname = etc_path / 'get_key_frames.bash'

class FramePair(collections.namedtuple('FramePair', 'frame_number timestamp')):
    pass

class KeyFrames:
    def __init__(self, arg, **kwargs):
        if isinstance(arg, (str, Path)):
            path = self.path = Path(arg)
            self.load_video(path)
        else:
            self.rows = arg
    def load_video(self, input_path, nframes=None, **kwargs):
        assert input_path.exists()
        if nframes:
            args = [ str(execname), '-n', str(nframes), str(input_path) ]
        else:
            args = [ str(execname), str(input_path) ]
        proc = run(args, stdout=subprocess.PIPE)
        assert (0 == proc.returncode)
        key_frame_filename, _ = proc.stdout.decode().split('\n')
        rows = self.rows = []
        y = rows.append
        with open(key_frame_filename, 'Ur') as fi:
            for line in fi:
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
