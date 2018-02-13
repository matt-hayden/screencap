#! /usr/bin/env python3


def pathsplit(text):
    p = text.rsplit('/', 1)
    if len(p) == 1:
        return '', p[0]
    return p


def splitext(text):
    p = text.rsplit('.', 1)
    if len(p) == 1:
        return p[0], ''
    return p[0], '.'+p[-1]


def clean_filename(text, dropchars='/;:<>&'):
    return ''.join('-' if (c in dropchars) else c for c in text.replace(' ', '_'))


