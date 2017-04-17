#!/usr/bin/env python3
import collections
from decimal import Decimal

#
def Tree():
	"""Initializes a Python tree with arbitrary depth.
	
	Member functions should be customized for adding nodes.
	"""
	return collections.defaultdict(Tree)
#
class Frame(collections.namedtuple('Frame', 'frame time')):
	"""Generic frame object for frame numbers paired with timestamps.
	"""
	def __int__(self):
		return int(self.frame or 0)
	def __float__(self):
		return float(self.time or 0.0)
	def __sub__(self, other):
		return Frame(self.frame-other.frame, self.time-other.time)
	def get_fps(self):
		if self.frame and self.time:
			return round((self.frame+1)/Decimal(self.time), 2)
#
def dequote(t, quote_chars='''"'`'''):
	if 2 < len(t):
		while t and (t[0] == t[-1]) and t[0] in quote_chars:
			t = t[1:-1]
	return t
#
