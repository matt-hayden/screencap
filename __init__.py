#!/usr/bin/env python3
import logging
import sys

__version__ = '0.2'
__all__ = ['__version__']

# basic logging:
logger = logging.getLogger(__name__) # always returns the same object
if __debug__:
	logging.basicConfig(level=logging.DEBUG)
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical

__all__.extend('debug warning info error panic'.split())

from .thumbnail import thumbnail, recurse

__all__.extend('thumbnail recurse'.split())
