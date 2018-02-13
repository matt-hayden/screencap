#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import json
import subprocess


class FFProbeHash(collections.namedtuple('ExtraDataHash', 'types value')):
    def __str__(self):
        return '%s:%X' %(':'.join(self.types), self.value)

def get_info(arg):
    """
    Process the output of the helpful ffprobe, which works on both local files and over HTTP
    """
    assert arg
    ffprobe_args = '-hide_banner -show_format -show_streams -show_chapters -show_data_hash SHA256 -print_format json'.split()
    debug("Running ffprobe %s %s", ' '.join(ffprobe_args), arg)
    proc = subprocess.Popen(['ffprobe']+ffprobe_args+[arg], stdout=subprocess.PIPE)
    probe_results_json, _ = proc.communicate()
    if (proc.returncode != 0) or not probe_results_json:
        error("error probing %s:" % arg)
        error("returned %d with output '%s'" % (proc.returncode, probe_results_json))
        return
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

    hashes = d['extradata_hashes'] = []
    for s in probe_results['streams']:
        h = s.pop('extradata_hash', None)
        if h:
            *hash_types, hash_s = h.split(':')
            hashes.append( FFProbeHash([s['codec_type']]+hash_types, int(hash_s, 16)) )
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
        probe_video_streams.sort(key=lambda vs: (-vs.get('bit_rate', 0), -vs.get('width', 0)))
        probe_video = probe_video_streams.pop(0)
    width = d['width'] = int(probe_video.pop('width'))
    height = d['height'] = int(probe_video.pop('height'))
    fps = d['fps'] = probe_video.pop('avg_frame_rate')
    nb_frames = d['nb_frames'] = probe_video.pop('nb_frames', None)
    return d
