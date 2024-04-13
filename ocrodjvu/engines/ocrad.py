# Copyright © 2010-2019 Jakub Wilk <jwilk@jwilk.net>
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

import codecs
import functools
import locale
import re
import sys
import shlex

from ocrodjvu.engines import common
from ocrodjvu import errors
from ocrodjvu import image_io
from ocrodjvu import ipc
from ocrodjvu import text_zones
from ocrodjvu import unicode_support
from ocrodjvu import utils


const = text_zones.const

_LANGUAGE_PATTERN = re.compile('^[a-z]{3}$')


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


_CHARACTER_RE = re.compile(r"^[0-9]+, '('|[^']*)'[0-9]+")


def scan(stream, settings):
    word_break_iterator = functools.partial(unicode_support.word_break_iterator, locale=settings.uax29)
    for line in stream:
        if line.startswith('#'):
            continue
        if line.startswith('source '):
            continue
        if line.startswith('total text blocks '):
            [n] = line.split()[3:]
            n = int(n)
            bbox = text_zones.BBox(*((0, 0) + settings.page_size))
            children = [_f for _f in (scan(stream, settings) for _ in range(n)) if _f]
            zone = text_zones.Zone(const.TEXT_ZONE_PAGE, bbox, children)
            zone.rotate(settings.rotation)
            return zone
        if line.startswith('text block '):
            n, x, y, w, h = list(map(int, line.split()[2:]))
            bbox = text_zones.BBox(x, y, x + w, y + h)
            [children] = [scan(stream, settings) for _ in range(n)]
            return text_zones.Zone(const.TEXT_ZONE_REGION, bbox, children)
        if line.startswith('lines '):
            [n] = line.split()[1:]
            n = int(n)
            return [_f for _f in (scan(stream, settings) for _ in range(n)) if _f]
        if line.startswith('line '):
            _, _, _, n, _, _ = line.split()
            n = int(n)
            children = [_f for _f in (scan(stream, settings) for _ in range(n)) if _f]
            if not children:
                return None
            bbox = text_zones.BBox()
            for child in children:
                bbox.update(child.bbox)
            children = text_zones.group_words(children, settings.details, word_break_iterator)
            return text_zones.Zone(const.TEXT_ZONE_LINE, bbox, children)
        line = line.lstrip()
        if line[0].isdigit():
            coords, line = line.split('; ', 1)
            x, y, w, h = list(map(int, coords.split()))
            bbox = text_zones.BBox(x, y, x + w, y + h)
            if line[0] == '0':
                # No interpretations have been proposed for this particular character.
                text = settings.replacement_character
            else:
                m = _CHARACTER_RE.match(line)
                if not m:
                    raise errors.MalformedOcrOutputError(f'bad character description: {line!r}')
                [text] = m.groups()
            return text_zones.Zone(const.TEXT_ZONE_CHARACTER, bbox, [text])
        raise errors.MalformedOcrOutputError(f'unexpected line: {line!r}')
    else:
        raise errors.MalformedOcrOutputError('unexpected EOF')


class Engine(common.Engine):
    name = 'ocrad'
    image_format = image_io.PNM

    executable = utils.Property('ocrad')
    extra_args = utils.Property([], shlex.split)
    replacement_character = utils.Property('\N{REPLACEMENT CHARACTER}', utils.str_as_unicode)

    def __init__(self, *args, **kwargs):
        common.Engine.__init__(self, **kwargs)
        try:
            self._languages = self._get_languages()
        except errors.UnknownLanguageListError:
            raise errors.EngineNotFoundError(self.name)

    def _get_languages(self):
        result = [self.default_language]
        try:
            with ipc.Subprocess(
                    [self.executable, '--charset=help'],
                    stdin=ipc.DEVNULL,
                    stdout=ipc.DEVNULL,
                    stderr=ipc.PIPE,
            ) as ocrad:
                try:
                    line = ocrad.stderr.read()
                    charsets = set(line.split()[1:])
                    if 'iso-8859-9' in charsets:
                        result += ['tur']
                finally:
                    try:
                        ocrad.wait()
                    except ipc.CalledProcessError:
                        pass
                    else:
                        raise errors.UnknownLanguageListError
        except OSError:
            raise errors.UnknownLanguageListError

        return result

    def check_language(self, language):
        if not _LANGUAGE_PATTERN.match(language):
            raise errors.InvalidLanguageIdError(language)
        if language not in self._languages:
            raise errors.MissingLanguagePackError(language)

    def list_languages(self):
        return iter(self._languages)

    def recognize(self, image, language, details=None, uax29=None):
        charset = 'iso-8859-15'
        if language == 'tur':
            charset = 'iso-8859-9'
        with ipc.Subprocess(
                [self.executable, '--charset', charset, '--format=utf8', '-x'] + self.extra_args + ['-', image.name],
                stdin=ipc.DEVNULL,
                stdout=ipc.PIPE,
        ) as worker:
            stdout = codecs.getreader(sys.stdout.encoding or locale.getpreferredencoding())(worker.stdout)
            return common.Output(
                stdout.read(),
                format_='orf',
            )

    def extract_text(self, stream, **kwargs):
        settings = ExtractSettings(**kwargs)
        settings.replacement_character = self.replacement_character
        scan_result = scan(stream, settings)
        return [scan_result.sexpr]
