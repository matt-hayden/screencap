#! /usr/bin/env python3
import logging
import sys

from .playlist import parse_playlist


def main(verbose=__debug__):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    execname, *args = sys.argv
    for arg in args:
        pl = parse_playlist(arg)
        print( '\n'.join(pl.get_lines()) )
