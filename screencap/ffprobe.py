#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import json
import subprocess
import urllib.parse

"""
Host status is tracked and, after a set number of failures, remote operations may be
"""
host_status = collections.Counter()


def get_info(arg, failures_allowed_per_host=5, urlparse=urllib.parse.urlparse):
    """
    Process the output of the helpful ffprobe, which works on both local files and over HTTP
    """
    assert arg
    u = urlparse(arg)
    h = u.netloc or None
    if h:
        h = None if (h.lower() == 'localhost') else h
        if h and (host_status[h] < -failures_allowed_per_host):
            warn("Ignoring host '%s' after %d errors", h, -host_status[h])
            return
    ffprobe_args = '-hide_banner -show_format -show_streams -show_chapters -show_data_hash SHA256 -print_format json'.split()
    debug("Running ffprobe %s %s", ' '.join(ffprobe_args), arg)
    proc = subprocess.Popen(['ffprobe']+ffprobe_args+[arg], stdout=subprocess.PIPE)
    probe_results_json, _ = proc.communicate()
    if (proc.returncode != 0) or not probe_results_json:
        error("error probing %s:" % arg)
        error("returned %d with output '%s'" % (proc.returncode, probe_results_json))
        if h:
            host_status[h] -= 1
        return
    if h:
        host_status[h] += 1
    probe_results = json.loads(probe_results_json.decode()) # is UTF-8?
    probe_format = probe_results['format']

    d = { 'filename': probe_format.pop('filename') }
    if 'tags' in probe_format:
        title = d['title'] = probe_format['tags'].pop('title', None)
    if 'size' in probe_format:
        file_size = d['file_size'] = int(probe_format.pop('size')) or None
    if 'duration' in probe_format:
        duration = d['duration'] = float(probe_format.pop('duration')) or None
    if 'bit_rate' in probe_format:
        bit_rate = d['bit_rate'] = float(probe_format.pop('bit_rate')) or None
    d['_ffprobe_meta'] = probe_results

    extradata_hashes = d['hashes'] = []
    for s in probe_results['streams']:
        h = s.pop('extradata_hash', None)
        if h:
            *hash_type, hash_s = h.split(':')
            extradata_hashes.append( (hash_type, int(hash_s, 16)) )
    probe_video_streams = [ s for s in probe_results['streams'] if s['codec_type'].startswith('video') ]
    probe_audio_streams = [ s for s in probe_results['streams'] if s['codec_type'].startswith('audio') ]
    probe_chapters = probe_results.get('chapters', None)
    if probe_chapters:
        probe_chapters.sort(key=lambda c: c['id'])
        d['chapters'] = probe_chapters
    
    n_video_streams = len(probe_video_streams)
    if (n_video_streams == 0):
        return d
    elif (n_video_streams == 1):
        probe_video = probe_video_streams.pop()
    else:
        probe_video_streams.sort(key=lambda vs: -vs['bit_rate'])
        probe_video = probe_video_streams.pop(0)
    width = d['width'] = int(probe_video.pop('width'))
    height = d['height'] = int(probe_video.pop('height'))
    fps = d['fps'] = probe_video.pop('average_frame_rate')
    nb_frames = d['nb_frames'] = probe_video.pop('nb_frames')
    return d
