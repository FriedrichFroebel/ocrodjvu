# encoding=UTF-8

# Copyright © 2008, 2009, 2010, 2011, 2013 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import contextlib
import shlex

from . import common
from . import tesseract
from .. import errors
from .. import image_io
from .. import ipc
from .. import utils

class Engine(common.Engine):

    name = 'ocropus'
    image_format = image_io.PNM
    output_format = 'html'

    executable = utils.property('ocroscript')
    tesseract_executable = utils.property('tesseract')
    extra_args = utils.property([], shlex.split)
    script_name = utils.property()
    has_charboxes = utils.property()

    def __init__(self, *args, **kwargs):
        assert args == ()
        common.Engine.__init__(self, **kwargs)
        self.tesseract = tesseract.Engine(executable=self.tesseract_executable)
        # Determine:
        # - if OCRopus is installed and
        # - which version we are dealing with
        if self.script_name is None:
            script_names = ['recognize', 'rec-tess']
        else:
            script_names = [self._script_name]
        for script_name in script_names:
            try:
                ocropus = ipc.Subprocess(['ocroscript', script_name],
                    stdout=ipc.PIPE,
                    stderr=ipc.PIPE,
                )
            except OSError:
                raise errors.EngineNotFound(self.name)
            try:
                found = ocropus.stdout.read(7) == 'Usage: '
            finally:
                try:
                    ocropus.wait()
                except ipc.CalledProcessError:
                    pass
            if found:
                self.script_name = script_name
                break
        else:
            raise errors.EngineNotFound(self.name)
        if self.has_charboxes is None and script_name == 'recognize':
            # OCRopus ≥ 0.3
            self.has_charboxes = True
        # Import hocr late, so that importing lxml is not triggered if Ocropus
        # is not used.
        from .. import hocr
        self._hocr = hocr

    @classmethod
    def get_default_language(cls):
        return tesseract.Engine.get_default_language()

    def check_language(self, language):
        return self.tesseract.check_language(language)

    def list_languages(self):
        return self.tesseract.list_languages()

    def recognize(self, image, language, details=None, uax29=None):
        hocr = self._hocr
        if details is None:
            details = hocr.TEXT_DETAILS_WORD
        def get_command_line():
            yield self.executable
            assert self.script_name is not None
            yield self.script_name
            if self.has_charboxes and details < hocr.TEXT_DETAILS_LINE:
                yield '--charboxes'
            for arg in self.extra_args:
                yield arg
            yield image.name
        ocropus = ipc.Subprocess(list(get_command_line()),
            stdout=ipc.PIPE,
            env=dict(tesslanguage=language),
        )
        try:
            return ocropus.stdout.read()
        finally:
            ocropus.wait()

    def extract_text(self, *args, **kwargs):
        return self._hocr.extract_text(*args, **kwargs)

# vim:ts=4 sw=4 et
