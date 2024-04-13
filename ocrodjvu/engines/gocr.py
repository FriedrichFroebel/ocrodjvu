# Copyright © 2010-2021 Jakub Wilk <jwilk@jwilk.net>
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

import functools
import re
import shlex

try:
    from lxml import etree
except ImportError:
    # noinspection PyPep8Naming
    from xml.etree import ElementTree as etree  # noqa: N813

from ocrodjvu.engines import common
from ocrodjvu import errors
from ocrodjvu import image_io
from ocrodjvu import ipc
from ocrodjvu import text_zones
from ocrodjvu import unicode_support
from ocrodjvu import utils


const = text_zones.const

_LANGUAGE_PATTERN = re.compile('^[a-z]{3}$')
_VERSION_RE = re.compile(r'\bgocr ([0-9]+).([0-9]+)\b')


class ExtractSettings:

    def __init__(self, rotation=0, details=text_zones.TEXT_DETAILS_WORD, uax29=None, page_size=None, **kwargs):
        self.rotation = rotation
        self.details = details
        if uax29 is not None:
            icu = unicode_support.get_icu()
            if uax29 is True:
                uax29 = icu.Locale('en-US-POSIX')
            else:
                uax29 = icu.Locale(uax29)
        self.uax29 = uax29
        self.page_size = page_size


def scan(stream, settings):
    word_break_iterator = functools.partial(unicode_support.word_break_iterator, locale=settings.uax29)
    stack = [[], [], []]
    for _, element in stream:
        if element.tag in {'barcode', 'img'}:
            continue
        if element.tag == 'page':
            if len(stack) != 1:
                raise errors.MalformedOcrOutputError('<page> at unexpected depth')
            children = stack.pop()
            bbox = text_zones.BBox(*((0, 0) + settings.page_size))
            zone = text_zones.Zone(const.TEXT_ZONE_PAGE, bbox, children)
            zone.rotate(settings.rotation)
            return zone
        elif element.tag == 'block':
            if len(stack) != 2:
                raise errors.MalformedOcrOutputError('<page> at unexpected depth')
            children = stack.pop()
            if len(children) == 0:
                raise errors.MalformedOcrOutputError('<block> has no children')
            bbox = text_zones.BBox()
            for child in children:
                bbox.update(child.bbox)
            zone = text_zones.Zone(const.TEXT_ZONE_REGION, bbox, children)
            stack[-1] += [zone]
        elif element.tag == 'line':
            if len(stack) != 3:
                raise errors.MalformedOcrOutputError('<line> at unexpected depth')
            children = stack.pop()
            if len(children) == 0:
                raise errors.MalformedOcrOutputError('<line> has no children')
            bbox = text_zones.BBox()
            for child in children:
                bbox.update(child.bbox)
            children = text_zones.group_words(children, settings.details, word_break_iterator)
            zone = text_zones.Zone(const.TEXT_ZONE_LINE, bbox, children)
            stack[-1] += [zone]
        elif element.tag in {'box', 'space'}:
            if len(stack) > 3:
                raise errors.MalformedOcrOutputError(f'<{element.tag}> at unexpected depth')
            while len(stack) < 3:
                stack += [[]]
            if element.tag == 'space':
                text = ' '
            else:
                text = element.get('value')
            x, y, w, h = (int(element.get(x)) for x in ('x', 'y', 'dx', 'dy'))
            bbox = text_zones.BBox(x, y, x + w, y + h)
            zone = text_zones.Zone(const.TEXT_ZONE_CHARACTER, bbox, [text])
            stack[-1] += [zone]
        else:
            raise errors.MalformedOcrOutputError(f'unexpected <{element.tag.encode("ASCII", "unicode-escape")}>')
    raise errors.MalformedOcrOutputError('<page> not found')


class Engine(common.Engine):
    name = 'gocr'
    image_format = image_io.PNM

    executable = utils.Property('gocr')
    extra_args = utils.Property([], shlex.split)

    def __init__(self, *args, **kwargs):
        common.Engine.__init__(self, *args, **kwargs)
        self._check_version()

    def _check_version(self):
        try:
            with ipc.Subprocess(
                    [self.executable],
                    stdin=ipc.DEVNULL,
                    stdout=ipc.DEVNULL,
                    stderr=ipc.PIPE,
            ) as gocr:
                line = gocr.stderr.read()
                m = _VERSION_RE.search(line.decode('UTF-8'))
                if not m:
                    raise errors.EngineNotFoundError(Engine.name)
                version = tuple(map(int, m.groups()))
                if version >= (0, 40):
                    return
                else:
                    raise errors.EngineNotFoundError(Engine.name)
        except OSError:
            raise errors.EngineNotFoundError(Engine.name)

    def check_language(self, language):
        if not _LANGUAGE_PATTERN.match(language):
            raise errors.InvalidLanguageIdError(language)
        if language != self.default_language:
            raise errors.MissingLanguagePackError(language)

    def list_languages(self):
        yield self.default_language

    def recognize(self, image, language, details=None, uax29=None):
        with ipc.Subprocess(
                [self.executable, '-i', image.name, '-f', 'XML'] + self.extra_args,
                stdin=ipc.DEVNULL,
                stdout=ipc.PIPE,
        ) as worker:
            return common.Output(
                worker.stdout.read(),
                format_='gocr.xml',
            )

    def extract_text(self, stream, **kwargs):
        settings = ExtractSettings(**kwargs)
        stream = etree.iterparse(stream)
        scan_result = scan(stream, settings)
        return [scan_result.sexpr]
