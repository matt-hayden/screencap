#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
from decimal import Decimal
import itertools
from pathlib import Path
import shlex
import urllib.parse

from .ffprobe import get_media_profile, get_media_profiles, FFProbeHash
from .util import *

"""
Helper functions:
"""
def file_key(entry):
    """
    For a PlaylistEntry, return a path.
    """
    if entry.remote:
        return entry.remote.path
    return entry.path
def file_order(entry):
    """
    For a PlaylistEntry, return its original order in the Playlist.
    """
    return entry['lineno']
def file_starttime_key(e):
    """
    For a PlaylistEntry, return an order by filename, then starting offset.
    """
    return file_key(e), e.get('start-time', 0) or 0
def host_key(entry):
    """
    For a PlaylistEntry, return a hostname:port, or empty string for local files.
    """
    if entry.remote:
        port = entry.remote.port or ''
        return entry.remote.hostname.lower()+(':%d' % port if port else '')
    return ''


class M3U_line(collections.namedtuple('M3U_line', 'text lineno')):
    def __str__(self):
        return self.text
class Comment(M3U_line):
    pass
class FileHeader(Comment):
    pass
class M3U_meta(Comment):
    def parse(self):
        if self.text.startswith('#EXT-X'):
            return self.text[1:].split(':', 1)
        return (self.text,)
class M3U_INF(M3U_meta):
    def parse(self, label='#EXTINF:'):
        assert self.text.startswith(label)
        s = self.text[len(label):].strip()
        if not s:
            return
        duration_s, *row = s.split(',')
        if ' ' in duration_s:
            duration_s, *parameters = shlex.split(duration_s)
            if all('=' in s for s in parameters):
                parameters = KVQ(s.split('=', 1) for s in parameters)
        else:
            parameters = None
        try:
            duration = Decimal(duration_s)
        except:
            info("Duration value '%s' ignored", duration_s)
            duration = None
        if (duration <= 0):
            duration = None
        return duration, parameters, row
class M3U_VLCOPT(M3U_meta):
    def parse(self, label='#EXTVLCOPT:'):
        assert self.text.startswith(label)
        s = self.text[len(label):]
        k, v = s.split('=', 1)
        if k in 'start-time stop-time'.split():
            return k, Decimal(v)
        return k, v.strip()
class M3U_GRP(M3U_meta):
    def parse(self, label='#EXTGRP:'):
        assert self.text.startswith(label)
        s = self.text[len(label):]
        return s.strip().capitalize()


def read_playlist(arg, mode='rU'):
    """
    Returns a sequence of tokens, in file order.

    Note that m3u files have several encodings; m3u8 files are UTF-8.
    """
    if isinstance(arg, (Path, str)):
        path = Path(arg)
        folder = path.parent
        with path.open(mode) as fi:
            lines = [ line.strip() for line in fi ]
    else:
        folder = None
        lines = [ line.strip() for line in arg ]
    lines = list(filter(None, lines))
    if not lines:
        error("Empty file")
        raise StopIteration()
    for lineno, line in enumerate(lines, start=1):
        if not line:
            continue
        if line.startswith('#'):
            if line.startswith('#EXTM3U'):
                yield FileHeader(line, lineno)
            elif line.startswith('#EXT-X'):
                yield M3U_meta(line, lineno)
            elif line.startswith('#EXTINF'):
                yield M3U_INF(line, lineno)
            elif line.startswith('#EXTGRP'):
                yield M3U_GRP(line, lineno)
            elif line.startswith('#EXTVLCOPT'):
                yield M3U_VLCOPT(line, lineno)
            else:
                yield Comment(line, lineno)
            continue
        if '://' in line:
            yield RemoteFile(line, lineno=lineno)
        else:
            yield LocalFile(line, lineno=lineno, folder=folder)


class Playlist(HasTitle, HasEntries):
    """
    .header         usually #EXTM3U
    .entries        entries in file order
    """
    def __init__(self, arg, **kwargs):
        HasTitle.__init__(self, **kwargs)
        HasEntries.__init__(self, **kwargs)
        self.header, self.parameters = None, []
        if isinstance(arg, (str, Path)):
            filename = self.path = Path(arg)
            self.folder = self.path.parent
            self.set_title('playlist_name', self.path.stem)
            self.from_iterable(read_playlist(self.path))
        else:
            self.from_iterable(read_playlist(arg))
    def _precompute_metadata(self):
        """
        Parallel-capable batch update of local files' metadata
        """
        return get_media_profiles(*set(e.path for e in self.entries if not e.remote))
    def by_host(self):
        """
        Yields groups of (hostname, True, entries) for remote, or (filename, False, entries) if local.
        """
        for hostname, es in itertools.groupby(sorted(self.entries, key=host_key), \
                key=host_key):
            if hostname:
                yield hostname, True, list(es)
            else:
                for filename, fes in itertools.groupby(sorted(es, key=file_key), \
                        key=file_key):
                    yield filename, False, list(fes)
    def from_iterable(self, iterable, start=1):
        """
        Import an iterable of tokens. Only tokens from read_playlist() are supported.
        """
        groups, comments, vlcopt = \
        [],     [],       KVQ()
        duration, parameters, tags = \
        None,     [],         []
        order = start
        for token in iterable:
            try:
                lineno = token.lineno
            except:
                lineno = token['lineno']
            if isinstance(token, FileHeader): # multiple may exist!
                self.header = token
            elif isinstance(token, M3U_INF):
                duration, parameters, new_tags = token.parse()
                tags.extend(new_tags)
            elif isinstance(token, M3U_GRP):
                groups.append(token.parse())
            elif isinstance(token, M3U_VLCOPT):
                k, v = token.parse()
                vlcopt[k] = v
            elif isinstance(token, M3U_meta): # subclass of Comment
                self.parameters.append((token.lineno, token.text))
            elif isinstance(token, Comment):
                comments.append(token)
            elif isinstance(token, PlaylistEntry):
                entry = token
                entry.file_order = order
                if comments:
                    entry['comments'], comments = comments, []
                if groups:
                    entry['groups'], groups = groups, set()
                if vlcopt:
                    entry.update(vlcopt)
                    vlcopt = KVQ()
                if duration:
                    entry.set_duration('from_VLCOPT', duration)
                    duration = None
                if parameters:
                    entry['parameters'], parameters = parameters, []
                if len(tags) == 1:
                    entry.set_title('from_playlist', tags.pop())
                elif len(tags) == 2:
                    debug("Assuming VLC Artist, Album = %s", tags)
                    entry['Artist'], entry['Album'] = tags
                    entry.set_title('tagged', entry['Album'])
                    tags = []
                elif tags:
                    debug("Multiple tags: %s", tags)
                    entry['tags'], tags = tags, []
                if ('start-time' in entry) or ('stop-time' in entry):
                    starttime = entry.get('start-time', Decimal('0'))
                    stoptime = entry.get('stop-time', None) or entry.get_duration()
                    if stoptime:
                        entry.set_duration(stoptime-starttime)
                entry.playlist = self
                self.entries.append(entry)
                order += 1
            else:
                error("Programming error: %s is unexpectedly type %s", token, type(token))
        self.nlines = lineno
    def to_m3u(self, **kwargs):
        """
        Generate a file representation of the Playlist.
        """
        lines = [ (file_order(e), e) for e in self ]
        lines.extend(self.parameters)
        lines.sort()
        for _, token in lines:
            if hasattr(token, 'to_m3u'):
                yield from token.to_m3u(**kwargs)
                yield ''
            else:
                yield token


class PlaylistEntry(HasTitle, HasDuration):
    def __init__(self, \
            title_default_order='playlist_name'.split(), \
            duration_default_order='from_metadata from_VLCOPT'.split()):
        """
        The arguments pre-populate entries in the titles and durations lists.
        These entries in increasing precedence
        """
        HasTitle.__init__(self, default_order=title_default_order)
        HasDuration.__init__(self, default_order=duration_default_order)
    def to_m3u(self, verbose=__debug__):
        if verbose:
            yield '# Titles:\t'+' -> '.join(filter(None, self._ordered_titles.values()))
            if self.get('Artist', None):
                yield '# Artist:\t"%s"' % self['Artist']
            d = self.get_duration()
            if d:
                yield '# Duration:\t%s' % time_s(d)
        if 'status' in self:
            yield '# Status: {1}\t{0!s}'.format(*self['status'])
        if verbose:
            if ('width' in self) or ('height' in self):
                yield '# Resolution:\t%.2f Mpx [%sx%s]' % (self.get('megapixels', 0), self.get('width', 0), self.get('height', 0))
            if 'file_size' in self:
                yield '# Size:\t\t{:,d} bytes'.format(self['file_size'])
            elif 'bit_rate' in self:
                yield '# Quality:\t{:,d} bit'.format(self['bit_rate'])
            yield '# Codecs:\t'+', '.join([self['video_codec']]+self['audio_codecs'])
            yield '#'
        if 'start-time' in self:
            yield '#EXTVLCOPT:start-time=%.6f' % self['start-time']
        if 'stop-time' in self:
            yield '#EXTVLCOPT:stop-time=%.6f' % self['stop-time']
        # VLC parses EXTINF lines as comma-separated duration, Artist, Track name
        if self.get_duration() or ('tags' in self) or ('Artist' in self):
            tags = self.get('tags', None) or \
                    [ self.get('Artist', ''), self.get_title() ]
            duration = self.get_duration()
            yield ('#EXTINF:%s,' % ('%.6f' % duration if duration else '-1')) \
                    +','.join(tags)
    def retrieve_metadata(self):
        d = { 'format': { 'filename':   str(self.remote or self.path),
                          'bit_rate':   self['bit_rate'],
                          'duration':   str(self.get_duration()),
                          'duration_t': time_s(self.get_duration()),
                          'tags': { 'title': self.get_title() },
                        },
              'streams': [ { 'codec_type': 'video', 'width': self['width'], 'height': self['height'] } ]
            }
        fs = self.get('file_size', 0)
        if fs:
            d['format']['size']     = fs
            d['format']['size_t']   = '{:,d} bytes'.format(fs)
        return d
    def update_metadata(self, d=None):
        """
        Populate object parts from ffprobe JSON output.
        """
        def video_stream_key(stream):
            try:
                x = float(stream.get('bit_rate', 0))
            except:
                x = 0
            try:
                y = int(stream.get('width', 0))
            except:
                y = 0
            return x, y

        if d is None:
            d = get_media_profile(self.remote or self.path)
        cs = d.pop('chapters', None)
        f  = d.pop('format', None)
        ss = d.pop('streams', None)
        if cs:
            cs.sort(key=lambda c: c['id'])
            self['chapters'] = cs
        if f:
            if 'tags' in f:
                t = f['tags'].pop('title', None)
                if t:
                    self.set_title('from_metadata', t)
            self['bit_rate'] = f['bit_rate']
            dur = f.pop('duration', None)
            if dur:
                self.set_duration('from_metadata', Decimal(dur))
            fs = f.pop('size', None)
            if fs:
                self['file_size'] = int(fs)
        if ss:
            vss, ass, oss = [], [], []
            hashes = self['extradata_hashes'] = []
            for s in ss:
                stype = s.pop('codec_type', None)
                h = s.pop('extradata_hash', None)
                if h:
                    *hash_types, hash_s = h.split(':')
                    hashes.append( FFProbeHash([stype]+hash_types, int(hash_s, 16)) )
                if stype == 'audio':
                    ass.append(s)
                elif stype == 'video':
                    vss.append(s)
                else:
                    oss.append(s)
            debug('%d video streams', len(vss))
            debug('%d audio streams', len(ass))
            debug('%d other streams', len(oss))
            lang = self['languages'] = []
            acs = self['audio_codecs'] = []
            for s in ass:
                t = s.get('tags', {}).pop('language', '')
                if t.strip():
                    lang.append(t)
                acs.append(s.pop('codec_name', None))
            primary_vs = max(vss, key=video_stream_key)
            if primary_vs:
                vss.remove(primary_vs)
                c = primary_vs.pop('codec_name', None)
                if c:
                    self['video_codec'] = c
                for k in 'width height avg_frame_rate nframes'.split():
                    v = primary_vs.pop(k, None)
                    if v:
                        self[k] = v
                debug("Unused video stream: %s", s)
                mp = self.get('width', 0)*self.get('height', 0)
                if mp:
                    self['megapixels'] = mp/1E6
            for s in vss:
                debug("Unused video stream: %s", s)
            for s in ass:
                debug("Unused audio stream: %s", s)
            for s in oss:
                debug("Unused stream: %s", s)


class LocalFile(PlaylistEntry, KVQ):
    def __init__(self, path, folder=None, **kwargs):
        super().__init__()
        self.remote = None
        self.update(kwargs)
        self.folder = Path(folder or '')
        self.set_path(self.folder / path)
    def set_path(self, path):
        path = self.path = Path(path)
        self.set_title('from_filename', path.stem)
    @property
    def filename(self):
        return self.path.name
    def to_m3u(self, **kwargs):
        yield from PlaylistEntry.to_m3u(self, **kwargs)
        yield str(self.path)
class RemoteFile(PlaylistEntry, KVQ):
    def __init__(self, arg=None, **kwargs):
        super().__init__()
        self.remote = None
        self.update(kwargs)
        if arg:
            self.url = arg
    @property
    def url(self):
        return urllib.parse.urlunsplit(self.remote)
    @url.setter
    def url(self, arg):
        self.remote = arg if isinstance(arg, urllib.parse.SplitResult) else urllib.parse.urlsplit(arg)
        self.set_title('from_url', self.filename.rsplit('.', 1)[0])
    @property
    def filename(self):
        if self.remote:
            return self.remote.path.rsplit('/', 1)[-1]
    @property
    def folder(self):
        if self.remote:
             s = self.remote.path.rsplit('/', 1)
             return s[0] if (1 < len(s)) else ''
    def to_m3u(self, **kwargs):
        yield from PlaylistEntry.to_m3u(self, **kwargs)
        yield str(self.url)

"""
Use either M3U or Playlist, based on namings within your application.
"""
M3U = Playlist
