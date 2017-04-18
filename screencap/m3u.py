#! /usr/bin/env python3

import collections
from decimal import Decimal
import os.path

try:
	from . import debug, info, warning, error, fatal
except:
	debug = info = warning = error = fatal = print


def sanitize_label(text):
	"""clipper.lua leaves default names with a funny pattern"""
	while text and text.endswith('(2)'):
		text = text[:3]
	return text
def sanitize_path(text):
	try:
		dirname, basename = os.path.split(text)
		if dirname and os.path.exists(dirname):
			info("Discarding existing path {}".format(dirname))
		else:
			debug("Discarding non-existent or empty path {}".format(dirname))
		return basename
	except:
		pass
	return text


class M3UError(Exception):
	pass


class M3UCut(collections.namedtuple('M3UCut', 'start_time stop_time label filename')):
	'''
	A cut has should have the following members:
		start_time
		stop_time
		label
		filename

	Optionally:
		name
		order
		duration (some cutting programs cannot accurately determine the end)
	'''
	@property
	def duration(self):
		return Decimal(self.stop_time) - Decimal(self.start_time)
	@staticmethod
	def from_lines(iterable, start_time=0, stop_time=None):
		for line in iterable.split('\n'):
			try:
				tag, expr = line.split(':', 1)
			except:
				tag, expr = '', line
			tag, expr = tag.strip(), expr.strip()
			if tag:
				if tag == '#EXTVLCOPT':
					k, v = expr.split('=', 1)
					if k == 'start-time':
						start_time = Decimal(v)
					elif k == 'stop-time':
						stop_time = Decimal(v)
					else:
						raise M3UError(line)
				elif tag == '#EXTINF':
					duration, label = expr.split(',', 1)
				elif tag.startswith('#'):
					debug("Ignoring comment {}".format(line))
				else:
					raise M3UError(line)
			elif expr:
				# filename
				filename = line
		return M3UCut(start_time, stop_time or Decimal(duration), sanitize_label(label), sanitize_path(filename))

def _parse(text):
	lines = text.split('\n\n')
	debug("Playlist has {} entries".format(len(lines) - 1))
	if lines[0].startswith('#EXTM3U'):
		lines.pop(0)
	else:
		warning("Unexpected first line {}".format(lines[0]))
	for entry in lines:
		if entry.strip():
			yield M3UCut.from_lines(entry)
#
def load(filename):
	with open(filename) as fi:
		return sorted(_parse(fi.read()), key=lambda row: row.start_time)


def form_m3u_entry(filename, start_time=-1, stop_time=-1, label=None, time_format='.3f'):
	assert filename
	if not label:
		dirname, basename = os.path.split(filename)
		filepart, ext = os.path.splitext(basename)
	if 0 < start_time:
		yield '#EXTVLCOPT:start-time={:{time_format}}'.format(start_time, time_format=time_format)
	if 0 < stop_time:
		yield '#EXTVLCOPT:stop-time={:{time_format}}'.format(stop_time, time_format=time_format)
	duration = stop_time-start_time
	yield '#EXTINF:{duration:{time_format}},{label}'.format(**locals())
	yield filename
def form_ExtPlaylist(cuts, filename='', label_format='Segment {n}'):
	yield '#EXTM3U'
	for n, cut in enumerate(cuts):
		yield '' # produce extra \n
		a, b = cut.start_time, cut.stop_time
		try:
			fn = cut.filename
		except:
			fn = None
		try:
			label = cut.label
		except:
			label = None
		yield from form_m3u_entry(fn or filename, a, b, label or label_format.format(**locals()) )


def save(cuts, fp, **kwargs):
	if hasattr(fp, 'write'):
		pos = fp.tell()
		fp.write('\n'.join(form_ExtPlaylist(cuts, **kwargs)) )
		return fp.tell() - pos
	else:
		_, basename = os.path.split(fp)
		filepart, ext = os.path.splitext(basename)
		if 'filename' not in kwargs:
			kwargs['filename']=filepart
		assert ext.upper() == '.M3U'
		with open(fp, 'w') as fo:
			return save(cuts, fo, **kwargs)


if __name__ == '__main__':
	import pprint
	import sys
	playlist = load(sys.argv[1])
	pprint.pprint(playlist)
