# Copyright © 2018 Jakub Wilk <jwilk@jwilk.net>
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
import io
import os
import shutil

from ocrodjvu import temporary
from ocrodjvu.cli import ocrodjvu

from tests.tools import remove_logging_handlers, try_run, TestCase


engines = 'tesseract', 'cuneiform', 'gocr', 'ocrad'


class OcrTestCase(TestCase):
    def _test_ocr(self, engine, layers):
        if not shutil.which(engine):
            raise self.SkipTest('{cmd} not found'.format(cmd=engine))
        remove_logging_handlers('ocrodjvu.')
        here = os.path.dirname(__file__)
        here = os.path.abspath(here)
        path = os.path.join(here, '..', 'data', 'alice.djvu')
        stdout = io.StringIO()
        stderr = io.StringIO()
        with temporary.directory() as tmpdir:
            tmp_path = os.path.join(tmpdir, 'tmp.djvu')
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = try_run(ocrodjvu.main, ['', '--engine', engine, '--render', layers, '--save-bundled', tmp_path, path])
        self.assertMultiLineEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertMultiLineEqual(stdout.getvalue(), '')

    def test_ocr(self):
        for engine in engines:
            for layers in 'mask', 'all':
                with self.subTest(engine=engine, layers=layers):
                    self._test_ocr(engine=engine, layers=layers)
