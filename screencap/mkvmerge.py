#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import json
import os, os.path
import shlex

from .converter import Converter
from .keyframes import KeyFrames
from .util import *

def to_json(obj):
    return json.dumps(obj, indent=2)


class MkvMergeConverter(Converter):
    execname = etc_path / 'mkvmerge.bash'
class MkvMergeSplitter(MkvMergeConverter):
    def __init__(self, entries, \
            input_path=None, \
            options_filename=None, \
            output_pattern=None, \
            keyframes=None, \
            nframes=None, \
            **options):
        if not input_path:
            ips = set(filter(None, (e['path'] for e in entries) ))
            input_path ,= ips
        if not keyframes:
            info("Detecting keyframes... (must read entire video)")
            keyframes = KeyFrames(input_path, nframes=nframes)
        for entry in entries:
            info("Playlist entry %s", entry['order'])
            assert os.path.samefile(entry.pop('path'), input_path)
            if 'output_path' not in entry:
                entry['output_path'] = os.path.join(entry.get('output_dir', ''), entry['output_filename'])
            if 'start-time' in entry:
                st = entry['start-time']
                keyframe_before, timestamp_before = keyframes.find(st)
                assert timestamp_before <= st
                if (timestamp_before < st):
                    info("Moving start time to previous keyframe")
                    entry['start-time_after-keyframe'] = st
                    entry['start-time'] = timestamp_before
        if not output_pattern:
            filepart, ext = os.path.splitext(input_path)
            ext = '.MKV'
            output_pattern = filepart+'-%03d'+ext
        self.input_path = input_path
        self.options_filename = options_filename or 'options'
        self.output_pattern = output_pattern
    def options_file_content(self, entries):
        parts = []
        for e in entries:
            begin = e.get('start-time', None)
            end = e.get('stop-time', None)
            parts.append('{!s}-{!s}'.format(str(begin)+'s' if begin else '', \
                    str(end)+'s' if end else ''))
        return [ '-o'
               , self.output_pattern
               , '--link'
               , '--split'
               , 'parts:'+','.join(parts)
               , self.input_path ]
    def commands(self, entries, sq=shlex.quote):
        execname = sq(str(self.execname))
        options_filename = sq(self.options_filename)
        yield ('< EOF cat > {options_filename}').format(**locals())
        yield to_json(self.options_file_content(entries))
        yield 'EOF'
        output_dirs = set( filter(None, (e.get('output_dir', None) for e in entries)) )
        if len(output_dirs):
            yield 'mkdir -p '+' '.join(sq(d) for d in output_dirs)
        yield ('{execname} @{options_filename}').format(**locals())
        for entry in entries:
            if entry.get('output_dir', None):
                output_path     = sq(entry['output_path'])
                output_filename = sq(entry['output_filename'])
                yield ('[[ -s {output_filename} ]] && mv {output_filename} {output_path}').format(**locals())
                del entry['output_dir']
            entry['path']       = entry.pop('output_path')
            entry['filename']   = entry.pop('output_filename')
            # before split
            for k in 'duration start-time stop-time'.split():
                entry.pop(k, None)
        yield 'mkdir -p delme covers'
        yield 'mv -i %s delme' % sq(self.input_path)
