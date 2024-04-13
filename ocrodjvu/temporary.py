# Copyright © 2009-2010 Jakub Wilk <jwilk@jwilk.net>
# Copyright © 2022-2024 FriedrichFroebel
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

import contextlib
import functools
import shutil
import tempfile as raw


file = functools.partial(raw.NamedTemporaryFile, prefix='ocrodjvu.')
name = functools.partial(raw.mktemp, prefix='ocrodjvu.')
# noinspection PyUnresolvedReferences,PyProtectedMember
wrapper = raw._TemporaryFileWrapper


@contextlib.contextmanager
def directory(*args, **kwargs):
    kwargs = dict(kwargs)
    kwargs.setdefault('prefix', 'ocrodjvu.')
    tmpdir = raw.mkdtemp(*args, **kwargs)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


__all__ = ['raw', 'file', 'directory', 'name', 'wrapper']
