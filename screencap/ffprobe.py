#! /usr/bin/env python3
import logging
logger = logging.getLogger()
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import json
import os.path
import subprocess


def get_info(arg):
    ffprobe_args = '-hide_banner -show_format -print_format json'.split()
    proc = subprocess.Popen(['ffprobe']+ffprobe_args+[arg], stdout=subprocess.PIPE)
    probe_results_json, _ = proc.communicate()
    if (proc.returncode != 0) or not probe_results_json:
        error("error probing %s:" % arg)
        error("returned %d with output '%s'" % (proc.returncode, probe_results_json))
        return
    probe_results = json.loads(probe_results_json.decode())
    probe_format = probe_results['format']
    filename = probe_format['filename']
    d = { 'filename': filename }
    title, ext = (filename.rsplit('/', 1)[-1]).rsplit('.', 1)
    if 'tags' in probe_format:
        title = d['title'] = probe_format['tags'].get('title', title)
    if 'size' in probe_format:
        file_size = d['file_size'] = int(probe_format['size'])
    if 'duration' in probe_format:
        duration = d['duration'] = float(probe_format['duration'])
    if 'bit_rate' in probe_format:
        bit_rate = d['bit_rate'] = float(probe_format['bit_rate'])
    return d
