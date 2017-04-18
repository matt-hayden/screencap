#! /usr/bin/env python3
import sys


import logging
logger = logging.getLogger('' if __name__ == '__main__' else __name__)
debug, info, warning, error, fatal = logger.debug, logger.info, logger.warning, logger.error, logger.critical

__all__ = 'debug warning info error fatal'.split()


if sys.stderr.isatty():
	import tqdm
	progress_bar = tqdm.tqdm
else:
	def progress_bar(iterable, **kwargs):
		return iterable
__all__ += ['progress_bar']


from .thumbnail import thumbnail, thumbdir, recurse

__all__.extend('thumbnail thumbdir recurse'.split())
