# encoding=UTF-8

# Copyright © 2010-2020 Jakub Wilk <jwilk@jwilk.net>
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

from ocrodjvu import errors
from ocrodjvu import temporary
from ocrodjvu.cli import ocrodjvu

from tests.tools import mock, remove_logging_handlers, require_locale_encoding, try_run, TestCase


class OcrodjvuTestCase(TestCase):
    engines = []

    def test_help(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(ocrodjvu.main, ['', '--help'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def test_version(self):
        """
        https://bugs.debian.org/573496
        """
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(ocrodjvu.main, ['', '--version'])
        self.assertEqual(rc, 0)
        self.assertEqual(stderr.getvalue(), '')
        self.assertNotEqual(stdout.getvalue(), '')

    def test_bad_options(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(ocrodjvu.main, [''])
        self.assertEqual(rc, errors.EXIT_FATAL)
        self.assertNotEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '')

    def test_list_engines(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(ocrodjvu.main, ['', '--list-engines'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.engines = stdout.getvalue().splitlines()

    def _test_list_languages(self, engine):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(ocrodjvu.main, ['', '--engine', engine, '--list-languages'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def test_list_languages(self):
        self.test_list_engines()
        self.assertTrue(self.engines)
        for engine in self.engines:
            with self.subTest(engine=engine):
                self._test_list_languages(engine)

    def test_nonascii_path(self):
        require_locale_encoding('UTF-8')  # djvused breaks otherwise.
        remove_logging_handlers('ocrodjvu.')
        here = os.path.dirname(__file__)
        here = os.path.abspath(here)
        path = os.path.join(here, '..', 'data', 'empty.djvu')
        stdout = io.StringIO()
        stderr = io.StringIO()
        with temporary.directory() as tmpdir:
            tmp_path = os.path.join(tmpdir, 'тмп.djvu')
            shutil.copy(path, tmp_path)
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = try_run(ocrodjvu.main, ['', '--engine', '_dummy', '--in-place', tmp_path])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue(), '')

    def test_bad_page_id(self):
        remove_logging_handlers('ocrodjvu.')
        here = os.path.dirname(__file__)
        here = os.path.abspath(here)
        path = os.path.join(here, '..', 'data', 'bad-page-id.djvu')
        stdout = io.StringIO()
        stderr = io.StringIO()
        with temporary.directory() as tmpdir:
            out_path = os.path.join(tmpdir, 'tmp.djvu')
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with mock.patch.object(ocrodjvu, 'SYSTEM_ENCODING', 'ASCII'):
                    rc = try_run(ocrodjvu.main, ['', '--engine', '_dummy', '--save-bundled', out_path, path])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue(), '')

# vim:ts=4 sts=4 sw=4 et
