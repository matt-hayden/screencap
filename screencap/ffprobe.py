#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import json
import subprocess


def get_info(arg):
    """
    Process the output of the helpful ffprobe, which works on both local files and over HTTP
    """
    ffprobe_args = '-hide_banner -show_format -show_streams -show_data_hash SHA256 -print_format json'.split()
    proc = subprocess.Popen(['ffprobe']+ffprobe_args+[arg], stdout=subprocess.PIPE)
    probe_results_json, _ = proc.communicate()
    if (proc.returncode != 0) or not probe_results_json:
        error("error probing %s:" % arg)
        error("returned %d with output '%s'" % (proc.returncode, probe_results_json))
        return
    probe_results = json.loads(probe_results_json.decode()) # is UTF-8?
    probe_format = probe_results['format']
    probe_video_streams = [ s for s in probe_results['streams'] if s['codec_type'].startswith('video') ]
    #probe_audio_streams = [ s for s in probe_results['streams'] if s['codec_type'].startswith('audio') ]

    # TODO: multiple video streams
    assert len(probe_video_streams) == 1
    probe_video = probe_video_streams.pop()

    d = { 'filename': probe_format.pop('filename') }
    if 'tags' in probe_format:
        title = d['title'] = probe_format['tags'].pop('title', None)
    if 'size' in probe_format:
        file_size = d['file_size'] = int(probe_format.pop('size')) or None
    if 'duration' in probe_format:
        duration = d['duration'] = float(probe_format.pop('duration')) or None
    if 'bit_rate' in probe_format:
        bit_rate = d['bit_rate'] = float(probe_format.pop('bit_rate')) or None
    if probe_video:
        width = d['width'] = int(probe_video.pop('width'))
        height = d['height'] = int(probe_video.pop('height'))
    d['_ffprobe_meta'] = probe_results
    return d
