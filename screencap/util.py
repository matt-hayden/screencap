# intended to 'from .util import *'

import collections
from datetime import datetime, timedelta
import os, os.path
from pathlib import Path
import shlex
import subprocess


module_path, _ = os.path.split(__file__)
etc_path = Path(module_path) / 'etc'
assert etc_path.exists()

now = datetime.now

def sq(arg):
    return shlex.quote(str(arg))

def run(command, **kwargs):
    c = [ str(w) for w in command ]
    return subprocess.run(c, **kwargs)

def time_s(n):
    if n is None:
        return ''
    return str(timedelta(seconds=float(n))).strip(' :0')

class KVQ(collections.OrderedDict):
    def get_latest(self):
        for k, v in self.items():
            pass
        return k, v
class Cache(KVQ):
    def resize(self, newsize):
        for _ in range(len(self)-newsize):
            self.popitem(last=False)


def firange(*args):
    """
    range(a, b, c) where c can be float
    
    Converges to yield a total of n=(b-a)/c values
    """
    if len(args) == 3:
        n, stop, step = args
        if n < stop:
            assert 0 < step
            while n < stop:
                yield round(n)
                n += step
        elif stop < n:
            assert step < 0
            while stop < n:
                yield round(n)
                n += step
    else:
        yield from range(*args)


class HasTitle:
    """
    """
    def __init__(self, default_order=[], **kwargs):
        if isinstance(default_order, str):
            default_order = default_order.split()
        self._ordered_titles = KVQ(( (k, None) for k in default_order))
    def get_title(self, key=None):
        if key:
            return self._ordered_titles.get(key, None)
        try:
            k, v = self._ordered_titles.get_latest()
            return v
        except:
            pass
    def set_title(self, *args):
        if len(args) == 1:
            return self.set_title(None, *args)
        k, v = args
        self._ordered_titles[k] = v
class HasDuration:
    """
    """
    def __init__(self, default_order=[], **kwargs):
        if isinstance(default_order, str):
            default_order = _default_order.split()
        self._ordered_durations = KVQ(( (k, None) for k in default_order))
    def get_duration(self, key=None):
        if key:
            return self._ordered_durations.get(key, None)
        try:
            k, v = self._ordered_durations.get_latest()
            return v
        except:
            pass
    def set_duration(self, *args):
        if len(args) == 1:
            return self.set_duration(None, *args)
        k, v = args
        self._ordered_durations[k] = v
class HasEntries:
    """
    """
    def __init__(self, **kwargs):
        self.entries = []
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def sort(self, *args, **kwargs):
        if self.entries:
            return self.entries.sort(*args, **kwargs)


def pathsplit(arg):
    p = Path(arg)
    return (arg.parent, arg.name)


def splitext(text):
    p = text.rsplit('.', 1)
    if len(p) == 1:
        return p[0], ''
    return p[0], '.'+p[-1]


def clean_filename(text, dropchars='/;:<>&'):
    if isinstance(text, str):
        return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))
    return clean_filename(str(text), dropchars=dropchars)
