#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import collections
import json
import os, os.path
import shlex

from .keyframes import KeyFrames
from .util import *

def to_json(obj):
    return json.dumps([str(_) for _ in obj], indent=2)

def sq(arg, **kwargs):
    return shlex.quote(str(arg))

class MkvMergeConverter:
    execname = etc_path / 'mkvmerge.bash'
    def to_script(self, head='#! /usr/bin/env bash\nset -e\n', **kwargs):
        return head+'\n'.join(self.get_commands(**kwargs))+'\n'
class MkvMergeSplitter(MkvMergeConverter):
    """
    
    """
    def __init__(self, entries):
        def start_stop_key(e):
            return e.get('start-time', 0), e.get('stop-time', 1E6)
        self.entries = sorted(entries, key=start_stop_key)
        "All entries expected to have the same input_path"
        self.input_filename ,= set(e.filename for e in self.entries)
        self.input_path ,= set(e.path for e in self.entries)
        self.options_filename = self.input_filename+'.options'
        fp, ext = os.path.splitext(self.input_filename)
        ext = '.MKV'
        pattern = self.filename_pattern = fp+'-%03d'+ext
        for n, e in enumerate(self.entries, start=1):
            if 'intermediate_filename' not in e:
               e['intermediate_filename'] = pattern % n
    def get_options(self, at_keyframes='before'):
        def get_timespan(e):
            begin = e.get('start-time', None)
            end = e.get('stop-time', None)
            return '{!s}-{!s}'.format(str(begin)+'s' if begin else '', \
                    str(end)+'s' if end else '')
        """
        mkvmerge splits at the first keyframe after the timecode. You may alter
        the split so that it aligns with a keyframe by passing one of:
            at_keyframe='before&after'
            at_keyframe='before' (the default)
            at_keyframe=None (saves a little time)
            at_keyframe='after' (valid, but useless and wasteful)
        """
        if at_keyframes:
            info("Detecting all keyframes for '%s'", self.input_path)
            keyframes = KeyFrames(self.input_path)
            if 'before' in at_keyframes:
                for e in self.entries:
                    if 'start-time' in e:
                        t = e['start-time']
                        e['start-time'], e['actual_start-time'] = \
                                keyframes.find(t).timestamp, t
            if 'after' in at_keyframes:
                for e in self.entries:
                    if 'stop-time' in e:
                        t = e['stop-time']
                        e['stop-time'], e['actual_stop-time'] = \
                                keyframes.find(t, direction=1).timestamp, t
        for p, n in zip(self.entries, self.entries[1:]):
            if 'stop-time' in p and 'start-time' in n:
                if p['stop-time'] > n['start-time']:
                    pd = p.get_duration()
                    nd = n.get_duration()
                    if (pd and nd) and (pd > nd):
                        info("Moving stop time %s -> %s", p['stop-time'], n['start-time'])
                        p['stop-time'] = n['start-time']
                    else:
                        info("Moving start time %s <- %s", p['stop-time'], n['start-time'])
                        n['start-time'] = p['stop-time']
        return [ '-o'
               , self.filename_pattern
               , '--link'
               , '--split'
               , 'parts:'+','.join(get_timespan(e) for e in self.entries)
               , self.input_path ]
    def get_commands(self, **kwargs):
        "Generate lines of sh code"
        yield "cat > %s << 'EOF'" % sq(self.options_filename)
        yield to_json(self.get_options(**kwargs))
        yield 'EOF'
        makeme = set()
        for e in self.entries:
            op = Path(e['output_path']).parent
            if not op.is_dir():
                makeme.add(op)
        if makeme:
            yield 'mkdir -p '+' '.join(sq(d) for d in makeme)
        yield '%s @%s || exit' % (sq(self.execname), sq(self.options_filename))
        for e in self.entries:
            yield '[[ -s {0} ]] && mv {0} {1} || echo "{1} failed!" >&2'.format( \
                    sq(e['intermediate_filename']), sq(e['output_path']))
        # custom:
        yield 'mkdir -p covers delme'
        yield 'mv -t delme %s' % sq(self.input_path)
