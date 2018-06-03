#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections

from . import *

from .ffmpeg import FFMpegSplitter
from .m3u import M3U
from .mkvmerge import MkvMergeSplitter

from .util import *


class NullSplitter:
    """
    Rump class for demonstrating the get_splitter function.
    """
    def __init__(self, entries):
        def start_stop_key(e):
            return e.get('start-time', 0), e.get('stop-time', 1E6)
        self.entries = sorted(entries, key=start_stop_key)
        "All entries expected to have the same input_path"
        self.input_filename ,= set(e.filename for e in self.entries)
        fp, ext = os.path.splitext(self.input_filename)
        pattern = fp+'-%03d'+ext
        for n, e in enumerate(self.entries, start=1):
            if 'intermediate_filename' not in e:
               e['intermediate_filename'] = pattern % n
    def get_commands(self):
        "Generate lines of sh code"
        yield 'cat << EOF'
        for e in self.entries:
            yield '%s -> %s -> %s' % \
                    (e.remote or e.path, \
                    e.pop('intermediate_filename'), \
                    e['output_path'])
        yield 'EOF'
    def to_script(self, head='#! /usr/bin/env bash\nset -e\n'):
        return head+'\n'.join(self.get_commands())+'\n'
        

def get_splitter(arg, \
        default_profiles=KVQ( [ ('(none)', NullSplitter) ] ), \
        **kwargs):
    """
    Yields at least one object with a .to_script() method.
    """
    if isinstance(arg, M3U):
        playlist = arg
    else:
        playlist_filename = arg
        playlist = parse_playlist(playlist_filename)

    if not len(playlist):
        warning("Empty playlist")
        raise StopIteration
    for filename_or_hostname, is_remote, entries in playlist.by_host():
        profiles = KVQ(default_profiles)
        if is_remote:
            basename = filename_or_hostname.path.rsplit('/', 1)[-1]
        else:
            profiles['mkvmerge'] = MkvMergeSplitter
            basename = filename_or_hostname.name
            _, ext = os.path.splitext(basename)
            force_ext = '.MKV' if ext.lower() in ['', '.mkv', '.mp4', '.webm'] else None
            filenames = collections.Counter()
            for entry in entries:
                entry['output_path'] = Path(entry['output_path'])
                fn = entry['output_path'].name
                fp, _ = os.path.splitext(fn)
                filenames[fp] += 1
            for n, entry in enumerate(entries, start=1):
                p = Path(entry['output_path'])
                fn = p.name
                fp, _ = os.path.splitext(fn)
                if 1 < filenames[fp]:
                    new_fp = '%s-%03d' % (fp, n)
                    debug("Renaming %s -> %s", fp, new_fp)
                    entry['output_path'] = p.parent/(new_fp+(force_ext or ext))
                elif force_ext:
                    entry['output_path'] = p.with_suffix(force_ext)
        basename = clean_filename(basename)
        profile, splitter = profiles.get_latest()
        info("Using splitter %s", profile)
        yield splitter(entries)
