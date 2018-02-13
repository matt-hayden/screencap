#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical


import collections
from datetime import datetime
import urllib.parse

from .util import *

now = datetime.now


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
    def parse(self, label='#EXTINF:'):
        assert self.text.startswith(label)
        s = self.text[len(label):]
        duration, *tags = s.split(',')
        return duration, tags
    def to_dict(self):
        duration, tags = self.parse()
        title = tags.pop(0)
        d = {}
        if (duration not in ['', '0', '-1']):
            d['duration'] = duration
        if title:
            d['title'] = title
        if tags:
            d['tags'] = tags
        return d
class M3U_VLCOPT(M3U_meta):
    def parse(self, label='#EXTVLCOPT:'):
        assert self.text.startswith(label)
        s = self.text[len(label):]
        k, v = s.split('=', 1)
        return k.strip(), v.strip()
class M3U_GRP(M3U_meta):
    def parse(self, label='#EXTGRP:'):
        assert self.text.startswith(label)
        s = self.text[len(label):]
        return s.strip().capitalize()
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
            elif line.startswith('#EXTVLCOPT'):
                yield M3U_VLCOPT(line, lineno)
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


class M3U_base:
    """
    The .entries iterable contains dictionaries with the following keys:
        filename:   if derived from url, un-percent-encoded
        comments:   non-metadata preceding location in m3u format
    And one of:
        path:       filesystem path
        url:        url tuple
    Optionally:
        duration:   number of seconds
        groups:     some sort of tagging
        tags:       tags other than title (may show up as album in VLC)
        title:      tagged title

    Internally:
        _m3u_meta:  metadata preserved in m3u format
        VLCOPT:     parameters injected by VLC
    """
    def __init__(self, *args):
        self.header, self.entries = None, []
        self.from_iterable(read_playlist(*args))
    def __len__(self):
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def sort(self, *args, **kwargs):
        if self.entries:
            return self.entries.sort(*args, **kwargs)
    def from_iterable(self, iterable):
        groups, meta, meta_lines, comments, vlcopt = set(), {}, [], [], collections.OrderedDict()
        order = 0
        for token in iterable:
            if isinstance(token, FileHeader): # multiple may exist in a file
                self.header = token
            elif isinstance(token, M3U_INF):
                meta_lines.append(token)
                meta.update(token.to_dict())
            elif isinstance(token, M3U_GRP):
                groups.add(token.parse())
            elif isinstance(token, M3U_VLCOPT):
                k, v = token.parse()
                vlcopt[k] = v
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
                    e['groups'], groups = groups, set()
                if vlcopt:
                    e['VLCOPT'], vlcopt = vlcopt, collections.OrderedDict()
                self.entries.append(e)
            else:
                error("Programming error: %s is unexpectedly type %s", token, type(token))
class M3U(M3U_base):
    def get_lines(self, verbose=False):
        if self.entries:
            yield '#EXTM3U'
            if verbose:
                yield '# %s' % now()
        for e in self.entries:
            yield ''
            duration = e.get('duration', None)
            title = e.get('title', None)
            vlcopt = e.get('VLCOPT', {})
            if 'playlist' in e:
                mock_title = e['playlist']
            else:
                mock_title, _ = splitext(e['filename'])
            tags = e.get('tags', [])
            groups = e.get('groups', [])
            if verbose:
                yield '#'
                yield '# "%s"' % (title or mock_title)
                if tags:
                    yield '# '+', '.join(tags)
                if 'status' in e:
                    yield '# %s status %s' % e['status'] # e['status'] is supposed to be a 2-tuple
                yield '#'
                #
                bit_rate	= e.get('bit_rate', None)
                chapters	= e.get('chapters', [])
                dimensions	= (e.get('width', 0), e.get('height', 0))
                file_size	= e.get('file_size', None)
                hashes  	= e.get('extradata_hashes', [])
                #
                if bit_rate:
                    assert isinstance(bit_rate, (int, float))
                    yield '# %.2f Mbit' % (bit_rate/1E6)
                if file_size is not None:
                    yield '# {:,d} bytes'.format(file_size)
                if any(dimensions):
                    yield '# %sx%s' % dimensions
                if chapters:
                    yield '#'
                    yield '# %d chapters' % len(chapters)
                if hashes:
                    yield '#'
                    yield '# extradata_hash found:'
                    for h in hashes:
                        yield '#   ' + str(h)
                    yield '#'
            for k, v in vlcopt.items():
                yield '#EXTVLCOPT:%s=%s' % (k, v)
            if duration or title or tags or vlcopt:
                yield '#EXTINF:%s,%s' % (duration or '-1', ','.join( ([title]+tags if title else tags) ))
            if groups:
                for g in sorted(groups):
                    yield '#EXTGRP:%s' % g
            if 'url' in e:
                yield e['url'].geturl()
            else:
                yield e.get('path', None) or e['playlist'] # TODO
    def to_file(self, filename, mode='w', **kwargs):
        with open(filename, mode) as fo:
            c = fo.write( '\n'.join(self.get_lines(**kwargs)) )
            fo.write('\n')
