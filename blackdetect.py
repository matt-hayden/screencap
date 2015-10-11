#!/usr/bin/env python3
import collections
from decimal import Decimal

from .utils import *

#
class BlackDetectCut(collections.namedtuple('BlackDetectCut', 'start stop')):
	@staticmethod
	def from_frame_desc(p1, p2):
		f1, d1 = p1
		f2, d2 = p2
		dd1, dd2 = d1['tags'], d2['tags']
		[t1], [t2] = dd1.values(), dd2.values()
		return BlackDetectCut( Frame(f1, t1), Frame(f2, t2) )
	@property
	def start_time(self):
		return self.start.time or None
	@property
	def stop_time(self):
		return self.stop.time or None
	@property
	def duration(self):
		return self.stop.time - self.start.time
def BlackDetectCutList(frames):
	assert not len(frames) % 2
	pairs = zip(frames[0::2], frames[1::2])
	return [ BlackDetectCut.from_frame_desc(*p) for p in pairs ]
#
def add(tree, path, leaf_value=None):
	key = path.pop(-1)
	leaf_value = dequote(leaf_value.strip())
	for node in path:
		if node.isdigit():
			node = int(node)
		tree = tree[node]
	if key:
		if leaf_value.isdigit():
			tree[key] = int(leaf_value)
		elif '.' in leaf_value:
			try:
				tree[key] = Decimal(leaf_value)
			except:
				tree[key] = leaf_value
		else:
			tree[key] = leaf_value
#
def parse_flat(iterable, result=Tree()): # see utils.py for Tree()
	for line in iterable:
		tpath, value = line.rstrip().split('=', 1)
		add(result, tpath.split('.'), value)
	return result
def parse(iterable):
	frame_dict = parse_flat(iterable)['frames']['frame']
	frames = sorted(frame_dict.items())
	first_frame = frames[0]
	if 'lavfi_black_start' in first_frame[1]['tags']:
		if int(first_frame[0]) < 15: # frame number
			frames.pop(0)
	last_frame = frames[-1]
	assert 'lavfi_black_start' in last_frame[1]['tags']
	cutlist = BlackDetectCutList(frames)
	_, last = cutlist[-1]
	return { 'fps': last.get_fps(), 'frames': cutlist }
#
def load(filename):
	with open(filename) as fi:
		return parse(fi)
if __name__ == '__main__':
	import pprint
	import sys
	bdd=load(sys.argv[1])
	print("{[fps]} frames per second".format(bdd))
	for n, cut in enumerate(bdd['frames']):
		if 0.5 < cut.duration:
			print(n, cut)
