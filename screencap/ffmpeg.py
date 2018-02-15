#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from datetime import timedelta
import os
import shlex
import subprocess
import sys
import tempfile

from .ffprobe import get_info
from .util import *


convert_execname = 'convert-im6'
ffmpeg_execname = 'ffmpeg'

arrow = '>' # '\u21e8'


def Popen(*args, **kwargs):
    debug("Running %s", ' '.join(shlex.quote(a) for a in args[0]))
    return subprocess.Popen(*args, **kwargs)


def make_tiles(input_path, output_filename=None, layout=(6,5), annotation=True, **kwargs):
    """
    input_path
    output_filename
    The FFMpeg tile filter defaults to 6 columns x 5 rows, which is a layout of (6, 5)

    the parameter 'filename' ought to be used only to override the text of the file's name

    annotation is (up to) 4 strings superimposed to each corner. The following strings are substituted:
    [ '{title}', '{dimensions}', '{file_size}', '{duration}' ]
    and this is this default.

    """
    ### Vital parameters
    media_info = kwargs or get_info(input_path) or {}
    filename = media_info.pop('filename', None) or pathsplit(input_path)[-1]
    ### Default arguments
    title = media_info.pop('title', None) or splitext(filename)[0]
    (start, stop), (duration, file_duration) = pop_start_stop_duration(media_info)
    file_size = media_info.pop('file_size', None)
    dimensions = None
    if ('width' in media_info) and ('height' in media_info):
        dimensions = "[%sx%s]" % (media_info['width'], media_info['height'])
    #
    if start or stop:
        ls = str(timedelta(seconds=start)).strip('0') if start else ''
        rs = str(timedelta(seconds=stop)).strip('0') if stop else str(timedelta(seconds=file_duration)).strip('0')
        lower_right = '%s%s%s' % (ls, arrow if ls else '', rs)
    elif duration:
        lower_right = str(timedelta(seconds=duration)).strip('0')
    else:
        lower_right = None
    if annotation == True:
        annotation = [ \
            title, \
            dimensions, \
            ("{:,d} bytes".format(file_size) if file_size else None), \
            lower_right ]
    if not any(annotation):
        annotation = None
    if not output_filename:
        output_filename = splitext(filename)[0]+'_screens.jpeg'
    ### ffmpeg options
    ffmpeg_args = [] #  ['-hide_banner']
    if annotation:
        _, output_filename, annotated_file = *tempfile.mkstemp(suffix='.png'), output_filename
        ffmpeg_args += ['-y']
    if not sys.stdin.isatty():
        ffmpeg_args += ['-nostdin']
    seconds_per_thumbnail = duration/(layout[0]*layout[1])
    ### Video processing
    info("Extracting %s thumbnails x %.2f seconds ~ %.2f duration", layout, seconds_per_thumbnail, duration)
    ffmpeg_args += '-skip_frame nokey -an -vsync 0'.split()
    if start:
        ffmpeg_args += [ '-ss', '{:.9f}'.format(start) ]
    ffmpeg_args += [ '-i', input_path ]
    if stop:
        ffmpeg_args += [ '-to', '{:.9f}'.format(stop) ]
    ffmpeg_args += [ '-vf', "select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,%f)',tile=%dx%d" % (seconds_per_thumbnail, layout[0], layout[1]) ]
    ffmpeg_args += '-frames:v 1'.split()
    proc = Popen( [ ffmpeg_execname, *ffmpeg_args, output_filename ] )
    proc.communicate()
    assert (proc.returncode == 0), ("%s failed on '%s'" % (ffmpeg_execname, input_path))
    if not annotation:
        return True
    ### Text overlay
    s = os.stat(output_filename)
    assert (0 < s.st_size), ("ffmpeg failed on '%s'" % input_path)
    convert_args = [ output_filename, '-resize', media_info.pop('output_dimensions', '2000000@>'), \
        '-fill', 'gray95', '-undercolor', '#00000080', \
        '-font', 'Palatino-Bold', '-pointsize', '28', '-antialias' ]
    for text, direction in zip(annotation, 'northwest northeast southwest southeast'.split()):
        if text:
            convert_args += [ '-gravity', direction, '-annotate', '+0+0', text.format(**locals()) ]
    proc = Popen( [ convert_execname, *convert_args, annotated_file ] )
    proc.communicate()
    os.unlink(output_filename)
    return (proc.returncode == 0)


def main(verbose=__debug__):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        make_tiles(input_filename=arg)

