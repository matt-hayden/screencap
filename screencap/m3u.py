#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections

class M3U_line(collections.namedtuple('M3U_line', 'text lineno')):
    def __str__(self):
        return self.text
class Comment(M3U_line):
    pass
class FileHeader(Comment):
    pass
class M3U_meta(Comment):
    def to_dict(self):
        assert self.text.startswith('#EXTINF:')
        s = self.text[len('#EXTINF:'):]
        duration, *tags = s.split(',')
        return { 'duration': None if (duration == '-1') else duration, \
                 'tags': tags }
class URI(M3U_line):
    pass


def read_file(arg, mode='rU'):
    """
    m3u files have several encodings
    m3u8 files are UTF-8
    """
    with open(arg, mode) as fi:
        lines = [ line.strip() for line in fi ]
    for lineno, line in enumerate(lines, start=1):
        if line:
            if line == '#EXTM3U':
                yield FileHeader(lines.pop(0), lineno)
            else:
                info("No header found")
            break
    else:
        error("Empty file")
        raise StopIteration()
    for lineno, line in enumerate(lines, start=lineno):
        if line.startswith('#'):
            if line.startswith('#EXT'):
                yield M3U_meta(line, lineno)
            else:
                yield Comment(line, lineno)
        elif line:
            yield URI(line, lineno)

class M3U:
    def __init__(self, arg):
        self.from_file(arg)
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def from_file(self, *args, **kwargs):
        self.header, self.entries = None, []
        meta, comments = {}, []
        for line in read_file(*args, **kwargs):
            if isinstance(line, FileHeader):
                self.header = line
            elif isinstance(line, M3U_meta):
                meta.update(line.to_dict())
            elif isinstance(line, Comment):
                comments.append(line)
            elif isinstance(line, URI):
                self.entries.append({'uri': str(line), 'm3u_meta': meta, 'comments': comments})
                meta, comments = {}, []
            else:
                error("Unknown parsed output: %s", line)


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    for arg in args:
        m = M3U(arg)
