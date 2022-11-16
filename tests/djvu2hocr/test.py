# encoding=UTF-8

# Copyright © 2010-2018 Jakub Wilk <jwilk@jwilk.net>
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
import shlex
import shutil
import sys

from lib import ipc
from lib import errors
from lib import temporary
from lib.cli import djvu2hocr

from tests.tools import mock, remove_logging_handlers, require_locale_encoding, sorted_glob, try_run, TestCase



class Djvu2hocrTestCase(TestCase):
    here = os.path.dirname(__file__)
    here = os.path.relpath(here)

    def test_help(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(djvu2hocr.main, ['', '--help'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def test_bad_options(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(djvu2hocr.main, [''])
        self.assertEqual(rc, errors.EXIT_FATAL)
        self.assertNotEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), '')

    def test_version(self):
        """
        https://bugs.debian.org/573496
        """
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = try_run(djvu2hocr.main, ['', '--version'])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

    def _test_from_file(self, base_filename, index):
        base_filename = os.path.join(self.here, base_filename)
        test_filename = '{base}.test{i}'.format(base=base_filename, i=index)
        djvused_filename = base_filename + '.djvused'
        with open(test_filename, 'rb') as fd:
            commandline = fd.readline()
            expected_output = fd.read()
        args = shlex.split(commandline.decode('UTF-8'))
        self.assertEqual(args[0], '#')
        with temporary.directory() as tmpdir:
            djvu_filename = os.path.join(tmpdir, 'empty.djvu')
            args += [djvu_filename]
            shutil.copy(
                os.path.join(os.path.dirname(__file__), '..', 'data', 'empty.djvu'),
                djvu_filename
            )
            ipc.Subprocess(['djvused', '-f', djvused_filename, '-s', djvu_filename]).wait()
            xml_filename = os.path.join(tmpdir, 'output.html')
            with open(xml_filename, 'w+b') as xml_file:
                xmllint = ipc.Subprocess(['xmllint', '--format', '-'], stdin=ipc.PIPE, stdout=xml_file, encoding='UTF-8')
                try:
                    with open(os.devnull, 'w') as null:
                        with mock.patch('sys.stdout', xmllint.stdin), mock.patch('sys.stderr', null):
                            with mock.patch.object(djvu2hocr.logger, 'handlers', []):
                                rc = try_run(djvu2hocr.main, args)
                finally:
                    xmllint.stdin.close()
                    try:
                        xmllint.wait()
                    except ipc.CalledProcessError:
                        # Raising the exception here is likely to hide the real
                        # reason of the failure.
                        pass
                self.assertEqual(rc, 0)
                xml_file.seek(0)
                output = xml_file.read()
        self.assertEqual(expected_output, output)

    def test_from_file(self):
        for test_filename in sorted_glob(os.path.join(here, '*.test[0-9]')):
            index = int(test_filename[-1])
            base_filename = os.path.basename(test_filename[:-6])
            with self.subTest(base_filename=base_filename, index=index):
                self._test_from_file(base_filename, index)

    def test_nonascii_path(self):
        require_locale_encoding('UTF-8')  # djvused breaks otherwise
        remove_logging_handlers('ocrodjvu.')
        here = os.path.dirname(__file__)
        here = os.path.abspath(here)
        path = os.path.join(here, '..', 'data', 'empty.djvu')
        stdout = io.StringIO()
        stderr = io.StringIO()
        with temporary.directory() as tmpdir:
            tmp_path = os.path.join(tmpdir, 'тмп.djvu')
            os.symlink(path, tmp_path)
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = try_run(djvu2hocr.main, ['', tmp_path])
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(rc, 0)
        self.assertNotEqual(stdout.getvalue(), '')

# vim:ts=4 sts=4 sw=4 et
