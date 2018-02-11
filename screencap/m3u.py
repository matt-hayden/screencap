#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import collections
import urllib.parse


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
        title = tags.pop(0)
        d = {}
        if (duration != '-1'):
            d['duration'] = duration
        if title:
            d['title'] = title
        if tags:
            d['tags'] = tags
        return d
class M3U_path(M3U_line):
    def to_dict(self, urlparse=urllib.parse.urlparse):
        parts = urlparse(self.text)
        *_, filename = parts.path.rsplit('/', 1)
        d = { 'path': self.text, 'filename': filename }
        if (parts.scheme in ('', 'file')) or not parts.hostname:
            info("Ignoring URL parts in %s", parts)
        else:
            d['url'] = parts
        return d


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
            yield M3U_path(line, lineno)


class M3U:
    """
    The .entries iterable contains dictionaries with the following keys:
        filename:   last relevant part of url
        comments:   non-metadata preceding location in m3u format
    Optionally:
        url:        unquoted url

    Unsupported:
        _m3u_meta:   metadata preserved in m3u format
    """
    def __init__(self, arg):
        self.from_file(arg)
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def from_file(self, *args, **kwargs):
        self.header, self.entries = None, []
        meta, meta_lines, comments = {}, [], []
        tokens = list(read_file(*args, **kwargs))
        for token in tokens:
            if isinstance(token, FileHeader):
                self.header = token
            elif isinstance(token, M3U_meta):
                meta_lines.append(token)
                meta.update(token.to_dict())
            elif isinstance(token, Comment):
                comments.append(token)
            elif isinstance(token, M3U_path):
                e = token.to_dict()
                e.update(meta)
                e['_m3u_meta'] = meta_lines
                if comments:
                    e['comments'] = comments
                self.entries.append(e)
                # reset
                meta, meta_lines, comments = {}, [], []
            else:
                error("Unknown parsed output: %s", token)
    def get_lines(self):
        if self.entries:
            yield '#EXTM3U'
        for e in self.entries:
            yield ''
            duration = e.get('duration', None)
            title = e.get('title', None)
            tags = e.get('tags', [])
            if duration or title or tags:
                title = title or e['filename'].rsplit('.', 1)[0]
                yield '#EXTINF:%s,%s' % (duration or '-1', ','.join([title]+tags))
            yield '%s' % e['path']
    def to_file(self, filename, mode='w'):
        with open(filename, mode) as fo:
            fo.write( '\n'.join(self.get_lines()) )
