# encoding=UTF-8

# Copyright © 2010-2021 Jakub Wilk <jwilk@jwilk.net>
#
# This file is part of ocrodjvu.
#
# ocrodjvu is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# ocrodjvu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.

import codecs
import contextlib
import functools
import glob
import locale
import logging
import os
from unittest import mock, SkipTest, TestCase as _TestCase


class TestCase(_TestCase):
    maxDiff = None
    SkipTest = SkipTest


@contextlib.contextmanager
def interim_environ(**override):
    keys = set(override)
    copy_keys = keys & set(os.environ)
    copy = {
        key: value
        for key, value in os.environ.items()
        if key in copy_keys
    }
    for key, value in override.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    try:
        yield
    finally:
        for key in keys:
            os.environ.pop(key, None)
        os.environ.update(copy)


def try_run(f, *args, **kwargs):
    """
    Catch SystemExit etc.
    """
    try:
        f(*args, **kwargs)
    except SystemExit as ex:
        return ex.code
    else:
        return 0

def sorted_glob(*args, **kwargs):
    return sorted(glob.iglob(*args, **kwargs))


def remove_logging_handlers(prefix):
    loggers = logging.Logger.manager.loggerDict.values()
    for logger in loggers:
        try:
            handlers = logger.handlers
        except AttributeError:
            continue
        for handler in handlers:
            if logger.name.startswith(prefix):
                logger.removeHandler(handler)


def require_locale_encoding(encoding):
    req_encoding = codecs.lookup(encoding).name
    locale_encoding = locale.getpreferredencoding()
    locale_encoding = codecs.lookup(locale_encoding).name
    if req_encoding != locale_encoding:
        raise SkipTest('locale encoding {enc} is required'.format(enc=encoding))


__all__ = [
    'mock',
    'TestCase',
    'SkipTest',
    'interim',
    'interim_environ',
    'remove_logging_handlers',
    'require_locale_encoding',
    'sorted_glob',
    'try_run',
]

# vim:ts=4 sts=4 sw=4 et
