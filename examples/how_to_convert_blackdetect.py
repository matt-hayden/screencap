#! /usr/bin/env python3
import os, os.path
import sys

from Screencap.blackdetect import load
from Screencap.m3u import save

file_in = sys.argv[1]
video_filename, _ = os.path.splitext(file_in)
file_out = video_filename+'.m3u'
cuts = load(file_in)['frames']
print(save(cuts, file_out, filename=video_filename))
