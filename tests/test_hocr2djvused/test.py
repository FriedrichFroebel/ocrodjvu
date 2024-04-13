# Copyright © 2010-2017 Jakub Wilk <jwilk@jwilk.net>
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
import re
import shlex
import warnings

import djvu.sexpr

from ocrodjvu import errors
from ocrodjvu.cli import hocr2djvused

from tests.tools import mock, sorted_glob, try_run, TestCase


class Hocr2djvusedTestCase(TestCase):
    here = os.path.dirname(__file__)
    here = os.path.relpath(here)

    def test_help(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(hocr2djvused.main, ['', '--help'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def test_version(self):
        # https://bugs.debian.org/573496
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(hocr2djvused.main, ['', '--version'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def test_bad_options(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(hocr2djvused.main, ['', '--bad-option'])
        self.assertEqual(rc, errors.EXIT_FATAL)
        self.assertNotEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '')

    @classmethod
    def normalize_sexpr(cls, match):
        return djvu.sexpr.Expression.from_string(match.group(1)).as_string(width=80)

    _djvused_text_re = re.compile('^([(].*)(?=^[.]$)', flags=(re.MULTILINE | re.DOTALL))

    @classmethod
    def normalize_djvused(cls, script):
        return cls._djvused_text_re.sub(cls.normalize_sexpr, script)

    def _test_from_file(self, base_filename, index, extra_args):
        base_filename = os.path.join(self.here, base_filename)
        test_filename = '{base}.test{i}'.format(base=base_filename, i=index)
        html_filename = '{base}.html'.format(base=base_filename)
        with open(test_filename, 'r') as fd:
            commandline = fd.readline()
            expected_output = fd.read()
        args = shlex.split(commandline) + shlex.split(extra_args)
        self.assertEqual(args[0], '#')
        stdout = io.StringIO()
        with open(html_filename, 'rb') as html_file:
            with mock.patch('sys.stdin', html_file), contextlib.redirect_stdout(stdout):
                with warnings.catch_warnings():
                    warnings.filterwarnings(action='ignore', message='Coercing non-XML name: xml:lang')
                    rc = try_run(hocr2djvused.main, args)
        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertMultiLineEqual(
            self.normalize_djvused(expected_output),
            self.normalize_djvused(output)
        )

    def _rough_test_from_file(self, base_filename, args):
        args = ['#'] + shlex.split(args)
        if base_filename.endswith(('cuneiform0.7', 'cuneiform0.8')):
            # Add dummy page-size information.
            args += ['--page-size=1000x1000']
        base_filename = os.path.join(self.here, base_filename)
        html_filename = '{base}.html'.format(base=base_filename)
        stdout = io.StringIO()
        with open(html_filename, 'rb') as html_file:
            with mock.patch('sys.stdin', html_file), contextlib.redirect_stdout(stdout):
                rc = try_run(hocr2djvused.main, args)
        self.assertEqual(rc, 0)
        output = stdout.getvalue()
        self.assertNotEqual(output, '')

    def test_from_file(self):
        rough_test_args = ['--details=lines']
        rough_test_args += [
            '--details={0}'.format(details) + extra
            for details in ('words', 'chars')
            for extra in ('', ' --word-segmentation=uax29')
        ]
        known_bases = set()
        for test_filename in sorted_glob(os.path.join(self.here, '*.test[0-9]')):
            index = int(test_filename[-1])
            base_filename = os.path.basename(test_filename[:-6])
            known_bases.add(base_filename)
            for extra_args in '', '--html5':
                with self.subTest(base_filename=base_filename, index=index, extra_args=extra_args):
                    self._test_from_file(base_filename, index, extra_args)
        for html_filename in sorted_glob(os.path.join(self.here, '*.html')):
            # For HTML files that have no corresponding .test* files, we just check
            # if they won't trigger any exception.
            base_filename = os.path.basename(html_filename[:-5])
            for args in rough_test_args:
                if base_filename not in known_bases:
                    for extra_args in '', ' --html5':
                        with self.subTest(base_filename=base_filename, args=args + extra_args):
                            self._rough_test_from_file(base_filename, args + extra_args)
