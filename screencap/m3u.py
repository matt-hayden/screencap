#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import collections
import urllib.parse


def url_parse(text, urlparse=urllib.parse.urlparse):
    parts = urlparse(text)
    server = parts.netloc.split(':', 1)[0]
    filename = parts.path.rsplit('/', 1)[-1]
    return { 'filename': filename, 'server': server }


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
class URL(M3U_line):
    pass


def read_file(arg, mode='rU'):
    """
    Generator yielding one object per non-blank line in input file.

    Note that m3u files have several encodings; m3u8 files are UTF-8.
    """
    with open(arg, mode) as fi:
        lines = [ line.strip() for line in fi ]
    if not lines:
        error("Empty file")
        raise StopIteration()
    for lineno, line in enumerate(lines, start=1):
        if line.startswith('#'):
            if line.startswith('#EXTM3U'):
                yield FileHeader(line, lineno)
            elif line.startswith('#EXT'):
                yield M3U_meta(line, lineno)
            else:
                yield Comment(line, lineno)
        elif line:
            yield URL(line, lineno)


class M3U:
    """
    The .entries iterable contains dictionaries with the following keys:
        url:        unquoted URL
        filename:   last relevant part of url
        m3u_meta:   metadata preserved in m3u format
        comments:   non-metadata preceding URL in m3u format
    """
    def __init__(self, arg):
        self.from_file(arg)
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def from_file(self, *args, **kwargs):
        self.header, self.entries = None, []
        meta, comments = {}, []
        lines = list(read_file(*args, **kwargs))
        for line in lines:
            if isinstance(line, FileHeader):
                self.header = line
            elif isinstance(line, M3U_meta):
                meta.update(line.to_dict())
            elif isinstance(line, Comment):
                comments.append(line)
            elif isinstance(line, URL):
                url = str(line)
                e = {'url': url, 'm3u_meta': meta, 'comments': comments}
                e.update(url_parse(url))
                self.entries.append(e)

                meta, comments = {}, []
            else:
                error("Unknown parsed output: %s", line)
    def get_lines(self):
        if self.entries:
            yield '#EXTM3U'
        for e in self.entries:
            yield ''
            title = e.get('title', None)
            duration = e.get('duration', None)
            if title or duration:
                yield 'EXTINF:%s,%s' % (duration or '-1', title or e['filename'].rsplit('.', 1)[0])
            yield '%s' % e['url']
    def to_file(self, filename, mode='w'):
        with open(filename, mode) as fo:
            fo.write( '\n'.join(self.get_lines()) )
