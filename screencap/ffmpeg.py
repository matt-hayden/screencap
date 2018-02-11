#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from datetime import timedelta
import os
import subprocess
import sys
import tempfile

from .ffprobe import get_info


convert_execname = 'convert-im6'


def make_tiles(input_path, media_info={}, n=6*5, output_filename=None, skip_intro=None, annotation=True, **kwargs):
    """
    media_info is a dictionary containing (at least) file duration, which is expected to be float() seconds, or a timedelta() object.

    annotation is (up to) 4 strings superimposed to each corner. The following strings are substituted:
    [ '{title}', '{dimensions}', '{file_size}', '{duration}' ]
    and this is this default.

    FFMpeg tile filter defaults to 6 columns x 5 rows
    """
    ### Vital parameters
    media_info = media_info or get_info(input_path) or {}
    filename = media_info.get('filename', None) or input_path.rsplit('/', 1)[-1]
    duration = media_info['duration']
    if isinstance(duration, timedelta):
        duration, duration_timestamp = duration.total_seconds(), duration
    else:
        if isinstance(duration, str):
            duration = float(duration)
        duration_timestamp = timedelta(seconds=duration)
    if duration <= 0:
        error("Could not determine file duration")
        return False
    ### Default arguments
    title = media_info.get('title', None) or filename.rsplit('.', 1)[0]
    file_size = media_info.get('file_size', None)
    dimensions = None
    if ('width' in media_info) and ('height' in media_info):
        dimensions = "[%sx%s]" % (media_info['width'], media_info['height'])
    #
    if annotation == True:
        annotation = [ \
            title, \
            dimensions, \
            ("{:,d} bytes".format(file_size) if file_size else None), \
            (str(duration_timestamp).strip('0') if duration else None) ]
    if not any(annotation):
        annotation = None
    if not output_filename:
        output_filename = filename.rsplit('.', 1)[0]+'_screens.jpeg'
    ### Options
    if skip_intro is None:
        skip_intro = (1000 < duration)
    if skip_intro is True:
        skip_intro = 30
    ffmpeg_args = ['-hide_banner']
    if annotation:
        output_filename, annotated_file = tempfile.mkstemp(suffix='.png')[1], output_filename
        ffmpeg_args += ['-y']
    if not sys.stdin.isatty():
        ffmpeg_args += ['-nostdin']
    if skip_intro:
        seconds_per_thumbnail = (duration-skip_intro)/n
        ffmpeg_args += ['-ss', str(skip_intro)]
    else:
        seconds_per_thumbnail = duration/n
    ### Video processing
    info("Extracting %d thumbnails x %.2f seconds ~ %.2f duration", n, seconds_per_thumbnail, duration)
    ffmpeg_args += '-skip_frame nokey -an -vsync 0'.split() \
        +[ '-i', input_path ] \
        +[ '-vf', "select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,%f)',tile" % (seconds_per_thumbnail) ]
    ffmpeg_args += '-frames:v 1'.split() \
        +[ output_filename ]
    debug("Running ffmpeg "+' '.join(ffmpeg_args))
    proc = subprocess.Popen(['ffmpeg']+ffmpeg_args)
    proc.communicate()
    if (proc.returncode != 0):
        error("ffmpeg failed on '%s'", input_path)
        return False
    if not annotation:
        return True
    ### Text overlay
    s = os.stat(output_filename)
    if (s.st_size <= 0):
        error("ffmpeg failed on '%s'", input_path)
        return False
    convert_args = [ output_filename, '-resize', '2000000@>', \
        '-fill', 'gray95', '-undercolor', '#00000080', \
        '-font', 'Palatino-Bold', '-pointsize', '28', '-antialias' ]
    for text, direction in zip(annotation, 'northwest northeast southwest southeast'.split()):
        if text:
            convert_args += [ '-gravity', direction, '-annotate', '+0+0', text.format(**locals()) ]
    convert_args += [ annotated_file ]
    debug("Running convert "+' '.join(convert_args))
    proc = subprocess.Popen([convert_execname]+convert_args)
    proc.communicate()
    os.unlink(output_filename)
    return (proc.returncode == 0)


def main(verbose=__debug__):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        make_tiles(input_filename=arg)

