#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import collections
import urllib.parse


def pathsplit(text):
    p = text.rsplit('/', 1)
    if len(p) == 1:
        return '', p[0]
    return p


def splitext(text):
    p = text.rsplit('.', 1)
    if len(p) == 1:
        return p[0], ''
    return p[0], '.'+p[-1]


class M3U_line(collections.namedtuple('M3U_line', 'text lineno')):
    def __str__(self):
        return self.text
class Comment(M3U_line):
    pass
class FileHeader(Comment):
    pass
class M3U_meta(Comment):
    pass
class M3U_INF(M3U_meta):
    def to_dict(self):
        assert self.text.startswith('#EXTINF:')
        s = self.text[len('#EXTINF:'):]
        duration, *tags = s.split(',')
        title = tags.pop(0)
        d = {}
        if (duration not in ['', '0', '-1']):
            d['duration'] = duration
        if title:
            d['title'] = title
        if tags:
            d['tags'] = tags
        return d
class M3U_GRP(M3U_meta):
    def to_dict(self):
        assert self.text.startswith('#EXTGRP:')
        s = self.text[len('#EXTGRP:'):]
        return { 'group': s.strip() }
class M3U_path(M3U_line):
    def to_dict(self, urlparse=urllib.parse.urlparse):
        url = urlparse(self.text)
        _, filename = pathsplit(url.path)
        if url.hostname:
            return { 'filename': urllib.parse.unquote(filename), 'url': url }
        else:
            return { 'filename': filename, 'path': self.text }
class M3U_playlist(M3U_path):
    def to_dict(self):
        return { 'filename': urllib.parse.unquote(self.text), 'playlist': self.text }


def read_playlist(arg, mode='rU'):
    """
    Generator yielding one object per non-blank line in input file.

    Note that m3u files have several encodings; m3u8 files are UTF-8.
    """
    if isinstance(arg, str):
        path = arg
        with open(path, mode) as fi:
            lines = [ line.strip() for line in fi ]
    else:
        lines = [ line.strip() for line in arg ]
    if not lines:
        error("Empty file")
        raise StopIteration()
    for lineno, line in enumerate(lines, start=1):
        if not line:
            continue
        if line.startswith('#'):
            if line.startswith('#EXTM3U'):
                yield FileHeader(line, lineno)
            elif line.startswith('#EXTINF'):
                yield M3U_INF(line, lineno)
            elif line.startswith('#EXTGRP'):
                yield M3U_GRP(line, lineno)
            else:
                yield Comment(line, lineno)
            continue
        p = M3U_path(line, lineno)
        d = p.to_dict()
        _, ext = splitext(d['filename'])
        if ext.lower() in '.m3u .m3u8'.split():
            yield M3U_playlist(line, lineno)
            continue
        yield p


class M3U:
    """
    The .entries iterable contains dictionaries with the following keys:
        filename:   if derived from url, un-percent-encoded
        comments:   non-metadata preceding location in m3u format
    And one of:
        path:       filesystem path
        url:        url tuple
    Optionally:
        duration:   number of seconds
        tags:       tags other than title (may show up as album in VLC)
        title:      tagged title

    Internally:
        _m3u_meta:   metadata preserved in m3u format
    """
    def __init__(self, *args):
        self.from_iterable(read_playlist(*args))
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def from_iterable(self, iterable):
        self.header, self.entries = None, []
        groups, meta, meta_lines, comments = [], {}, [], []
        order = 0
        for token in iterable:
            if isinstance(token, FileHeader):
                self.header = token
            elif isinstance(token, M3U_INF):
                meta_lines.append(token)
                meta.update(token.to_dict())
            elif isinstance(token, M3U_GRP):
                groups.append(token.to_dict()['group'])
            elif isinstance(token, Comment):
                comments.append(token)
            elif isinstance(token, M3U_path): # includes playlists
                e = token.to_dict()
                if 'playlist' in e:
                    e['url'] = urllib.parse.urlparse(e['playlist']) # TODO
                e.update(meta)
                meta = {}
                e['_m3u_meta'], meta_lines = meta_lines, []
                e['order'] = order
                order += 1
                if comments:
                    e['comments'], comments = comments, []
                if groups:
                    e['groups'], groups = groups, []
                self.entries.append(e)
            else:
                error("Programming error: %s is unexpectedly type %s", token, type(token))
    def get_lines(self, verbose=False):
        if self.entries:
            yield '#EXTM3U'
        for e in self.entries:
            yield ''
            duration = e.get('duration', None)
            title = e.get('title', None)
            if 'playlist' in e:
                mock_title = e['playlist']
            else:
                mock_title, _ = splitext(e['filename'])
            tags = e.get('tags', [])
            groups = e.get('groups', [])
            if verbose:
                yield '#'
                yield '# %s' % (title or mock_title)
                if 'status' in e:
                    yield '# Status %s' % e['status']
                yield '#'
                bit_rate = e.get('bit_rate', None)
                dimensions = (e.get('width', 0), e.get('height', 0))
                if bit_rate:
                    yield '# %.2f Mbit' % bit_rate/1E6
                if any(dimensions):
                    yield '# %sx%s' % dimensions
            if duration or title or tags:
                yield '#EXTINF:%s,%s' % (duration or '-1', ','.join( ([title]+tags if title else tags) ))
            if groups:
                yield '#EXTGRP:%s' % ', '.join(groups)
            yield '%s' % (e['url'].geturl() if 'url' in e else e.get('path', None) or e['playlist'])
    def to_file(self, filename, mode='w'):
        with open(filename, mode) as fo:
            fo.write( '\n'.join(self.get_lines()) )
    def sort(self, *args, **kwargs):
        if self.entries:
            return self.entries.sort(*args, **kwargs)
