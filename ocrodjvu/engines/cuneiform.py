# Copyright © 2010-2022 Jakub Wilk <jwilk@jwilk.net>
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
import locale
import os
import re
import shlex
import sys
import warnings

from ocrodjvu.engines import common
from ocrodjvu import errors
from ocrodjvu import image_io
from ocrodjvu import ipc
from ocrodjvu import iso639
from ocrodjvu import temporary
from ocrodjvu import utils


_LANGUAGE_PATTERN = re.compile('^[a-z]{3}(?:[+][a-z]{3})*$')
_LANGUAGE_INFO_PATTERN = re.compile(r"^Supported languages: (.*)[.]$")


class Engine(common.Engine):
    name = 'cuneiform'
    image_format = image_io.BMP
    needs_utf8_fix = True

    executable = utils.Property('cuneiform')
    extra_args = utils.Property([], shlex.split)
    fix_html = utils.Property(0, int)
    # fix_html currently does nothing, but we left it, as it might become useful again at some point in the future.

    def __init__(self, *args, **kwargs):
        common.Engine.__init__(self, *args, **kwargs)
        self._user_to_cuneiform = None  # To be defined later.
        self._cuneiform_to_iso = None  # To be defined later.
        try:
            self._languages = list(self._get_languages())
        except errors.UnknownLanguageListError:
            raise errors.EngineNotFoundError(self.name)
        # Import hocr late, so that lxml is imported only when needed.
        from ocrodjvu import hocr
        self._hocr = hocr

    def _get_languages(self):
        try:
            with ipc.Subprocess(
                    [self.executable, '-l'],
                    stdin=ipc.DEVNULL,
                    stdout=ipc.PIPE,
            ) as cuneiform:
                stdout = codecs.getreader(sys.stdout.encoding or locale.getpreferredencoding())(cuneiform.stdout)
                self._cuneiform_to_iso = {}
                self._user_to_cuneiform = {}
                try:
                    for line in stdout:
                        m = _LANGUAGE_INFO_PATTERN.match(line)
                        if m is None:
                            continue
                        codes = m.group(1).split()
                        for code in codes:
                            if code == 'ruseng':
                                iso_code = 'rus+eng'
                                # For compatibility with ocrodjvu ≤ 0.7.14:
                                self._user_to_cuneiform[frozenset(['rus-eng'])] = code
                            elif code == 'slo':
                                if 'slv' not in codes:
                                    # Cuneiform ≤ 1.0 mistakenly uses `slo` as language code for Slovenian.
                                    # https://bugs.launchpad.net/cuneiform-linux/+bug/707951
                                    iso_code = 'slv'
                                else:
                                    # Both `slo` and `slv` are available. Let's guess that the former means Slovak.
                                    iso_code = 'slk'
                            else:
                                try:
                                    iso_code = str.join('+', (
                                        iso639.b_to_t(c) for c in code.split('_')
                                    ))
                                except ValueError:
                                    warnings.warn(
                                        f'unparsable language code: {code!r}',
                                        category=RuntimeWarning,
                                        stacklevel=2
                                    )
                            self._cuneiform_to_iso[code] = iso_code
                            self._user_to_cuneiform[frozenset(iso_code.split('+'))] = code
                            yield iso_code
                        return
                finally:
                    try:
                        cuneiform.wait()
                    except ipc.CalledProcessError:
                        pass
                    else:
                        raise errors.UnknownLanguageListError
        except OSError:
            raise errors.UnknownLanguageListError

        raise errors.UnknownLanguageListError

    def check_language(self, language):
        if language == 'slo':
            # Normally we accept Cuneiform-specific language code. This is an
            # exception: `slo` is Slovenian in Cuneiform ≤ 1.0, but it is Slovak
            # according to ISO 639-2.
            language = 'slk'
        else:
            language = self.cuneiform_to_iso(language)
        language = self.normalize_iso(language)
        if not _LANGUAGE_PATTERN.match(language):
            raise errors.InvalidLanguageIdError(language)
        if language not in self._languages:
            raise errors.MissingLanguagePackError(language)

    def list_languages(self):
        return iter(self._languages)

    def user_to_cuneiform(self, language):
        language_set = frozenset(
            iso639.b_to_t(code, permissive=True)
            for code in language.split('+')
        )
        return self._user_to_cuneiform.get(language_set, language)

    def cuneiform_to_iso(self, language):
        return self._cuneiform_to_iso.get(language, language)

    def normalize_iso(self, language):
        language = self.user_to_cuneiform(language)
        language = self.cuneiform_to_iso(language)
        return language

    def recognize(self, image, language, *args, **kwargs):
        with temporary.directory() as hocr_directory:
            # A separate non-world-writable directory is needed, as Cuneiform
            # can create additional files, e.g. images.
            hocr_file_name = os.path.join(hocr_directory, 'ocr.html')
            with ipc.Subprocess(
                    [
                        self.executable,
                        '-l', self.user_to_cuneiform(language),
                        '-f', 'hocr',
                        '-o', hocr_file_name
                    ] + self.extra_args + [image.name],
                    stdin=ipc.DEVNULL,
                    stdout=ipc.DEVNULL,
            ):
                # Implicitly call `wait()` on `__exit__`.
                pass
            with open(hocr_file_name, 'r') as hocr_file:
                return common.Output(
                    hocr_file.read(),
                    format_='html',
                )

    def extract_text(self, *args, **kwargs):
        return self._hocr.extract_text(*args, **kwargs)
