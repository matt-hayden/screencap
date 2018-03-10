#! /usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

import collections
import copy
import json
import subprocess

from .util import *

media_profiler_execname = etc_path / 'json_media_info.bash'
assert media_profiler_execname.exists()


class FFProbeHash(collections.namedtuple('ExtraDataHash', 'types value')):
    def __str__(self):
        return '%s:%X' %(':'.join(self.types), self.value)


def get_media_profile(arg, **kwargs):
    """
    Retrieve a structure of media metadata
    """
    return get_media_profiles(arg)[str(arg)]
def get_media_profiles(*args, refresh=False, \
        cache=Cache(), deepcopy=copy.deepcopy, \
        **kwargs):
    def media_profiler(*args, **kwargs):
        proc = run([media_profiler_execname]+list(args), \
                stdout=subprocess.PIPE)
        assert proc.returncode == 0
        d = json.loads(proc.stdout.decode())
        for arg in args:
            if arg not in d:
                error("'%s' skipped", arg)
        return d
    args = [ str(a) for a in args ]
    not_found = set(args)
    if (cache is not None) and not refresh:
        not_found -= set(cache)
    if not_found:
        debug("Reading "+', '.join("'%s'" % f for f in not_found))
        cache.update(media_profiler(*not_found, **kwargs))
    return { k: copy.deepcopy(cache[k]) for k in args }
