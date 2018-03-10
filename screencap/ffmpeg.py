#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import json
import os, os.path
from pathlib import Path
import subprocess
import sys
import tempfile

from .util import *


ffmpeg_execname = etc_path / 'ffmpeg.bash'

arrow = '>' # '\u21e8'

class FFMpegConverter:
    execname = etc_path / 'ffmpeg.bash'
    def to_script(self, head='#! /usr/bin/env bash\nset -e\n', **kwargs):
        return head+'\n'.join(self.get_commands(**kwargs))+'\n'
class FFMpegSplitter(FFMpegConverter):
    def __init__(self, entries):
        def start_stop_key(e):
            return e.get('start-time', 0), e.get('stop-time', 1E6)
        self.entries = sorted(entries, key=start_stop_key)
    def get_commands(self, **kwargs):
        "Generate lines of sh code"
        for e in self.entries:
            op = Path(e['output_path']).parent
            if not op.is_dir():
                makeme.add(op)
        if len(makeme):
            yield 'mkdir -p '+' '.join(sq(d) for d in makeme)
        for e in self.entries:
            begin, end = entry.get('start-time', None), entry.get('stop-time', None)
            if begin or end:
                line = '{0.execname} -i {1}'.format(self, e.remote or e.path)
                if begin:
                    line += ' -ss {!s}'.format(begin)
                if end:
                    line += ' -to {!s}'.format(end)
                line += ' -codec copy {output_path} || echo "{output_path} failed!" >&2'.format(**e)
                yield line
        local_files = list(filter(None, (e.path for e in entries)))
        if local_files:
            yield 'mkdir -p delme covers'
            yield 'mv -i -t delme '+' '.join(sq(f) for f in local_files)

screencap_execname = etc_path / 'screencap.bash'
assert screencap_execname.exists()

def get_screencap_commands(*input_args, head='#! /usr/bin/env bash\nset -e\n', **kwargs):
    assert input_args
    command = [sq(screencap_execname)]+[ sq(a) for a in input_args ]
    yield head
    if kwargs:
        d = kwargs
        yield ' '.join(command)+" << 'EOF'"
        yield json.dumps(d, indent=2)
        yield 'EOF'
    else:
        yield ' '.join(command)
