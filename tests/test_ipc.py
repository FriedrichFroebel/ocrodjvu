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

import errno
import os
import signal

from ocrodjvu import ipc
from ocrodjvu import temporary

from tests.tools import interim_environ, TestCase


class ExceptionsTestCase(TestCase):
    def test_sigint(self):
        ex = ipc.CalledProcessInterrupted(signal.SIGINT, 'eggs')
        self.assertEqual(str(ex), "Command 'eggs' was interrupted by signal SIGINT")
        self.assertTrue(ex.by_user)

    def test_sigabrt(self):
        ex = ipc.CalledProcessInterrupted(signal.SIGABRT, 'eggs')
        self.assertEqual(str(ex), "Command 'eggs' was interrupted by signal SIGABRT")
        self.assertFalse(ex.by_user)

    def test_sigsegv(self):
        ex = ipc.CalledProcessInterrupted(signal.SIGSEGV, 'eggs')
        self.assertEqual(str(ex), "Command 'eggs' was interrupted by signal SIGSEGV")
        self.assertFalse(ex.by_user)

    def test_invalid_signo(self):
        # signal.NSIG is guaranteed not be a correct signal number.
        ex = ipc.CalledProcessInterrupted(signal.NSIG, 'eggs')
        self.assertEqual(str(ex), f"Command 'eggs' was interrupted by signal {signal.NSIG}")
        self.assertFalse(ex.by_user)


class InitExceptionTestCase(TestCase):
    """
    https://bugs.python.org/issue32490
    """

    def test_init_exc(self):
        prog = 'ocrodjvu-nonexistent'
        with self.assertRaises(EnvironmentError) as ecm:
            ipc.Subprocess([prog])
        msg = f'[Errno {errno.ENOENT}] {os.strerror(errno.ENOENT)}: {prog!r}'
        self.assertEqual(str(ecm.exception), msg)


class WaitTestCase(TestCase):
    def test0(self):
        child = ipc.Subprocess(['true'])
        child.wait()

    def test1(self):
        child = ipc.Subprocess(['false'])
        with self.assertRaises(ipc.CalledProcessError) as ecm:
            child.wait()
        message = str(ecm.exception)
        self.assertEqual(message, "Command 'false' returned non-zero exit status 1.")

    def _test_signal(self, name):
        child = ipc.Subprocess(['cat'], stdin=ipc.PIPE)  # Any long-standing process would do.
        os.kill(child.pid, getattr(signal, name))
        with self.assertRaises(ipc.CalledProcessInterrupted) as ecm:
            child.wait()
        self.assertEqual(str(ecm.exception), "Command 'cat' was interrupted by signal " + name)
        child.stdin.close()

    def test_wait_signal(self):
        for name in 'SIGINT', 'SIGABRT', 'SIGSEGV':
            with self.subTest(name=name):
                self._test_signal(name)


class EnvironmentTestCase(TestCase):
    """
    https://bugs.debian.org/594385
    """

    def test1(self):
        with interim_environ(ocrodjvu='42'):
            child = ipc.Subprocess(
                ['sh', '-c', 'printf $ocrodjvu'],
                stdout=ipc.PIPE, stderr=ipc.PIPE,
            )
            stdout, stderr = child.communicate()
            self.assertEqual(stdout, b'42')
            self.assertEqual(stderr, b'')

    def test2(self):
        with interim_environ(ocrodjvu='42'):
            child = ipc.Subprocess(
                ['sh', '-c', 'printf $ocrodjvu'],
                stdout=ipc.PIPE, stderr=ipc.PIPE,
                env={},
            )
            stdout, stderr = child.communicate()
            self.assertEqual(stdout, b'42')
            self.assertEqual(stderr, b'')

    def test3(self):
        with interim_environ(ocrodjvu='42'):
            child = ipc.Subprocess(
                ['sh', '-c', 'printf $ocrodjvu'],
                stdout=ipc.PIPE, stderr=ipc.PIPE,
                env=dict(ocrodjvu='24'),
            )
            stdout, stderr = child.communicate()
            self.assertEqual(stdout, b'24')
            self.assertEqual(stderr, b'')

    def test_path(self):
        path = os.getenv('PATH')
        with temporary.directory() as tmpdir:
            command_name = temporary.name(dir=tmpdir)
            command_path = os.path.join(tmpdir, command_name)
            with open(command_path, 'wt') as fd:
                fd.write('#!/bin/sh\n')
                fd.write('printf 42')
            os.chmod(command_path, 0o700)
            path = str.join(os.pathsep, [tmpdir, path])
            with interim_environ(PATH=path):
                child = ipc.Subprocess(
                    [command_name],
                    stdout=ipc.PIPE, stderr=ipc.PIPE,
                )
                stdout, stderr = child.communicate()
                self.assertEqual(stdout, b'42')
                self.assertEqual(stderr, b'')

    def _test_locale(self):
        child = ipc.Subprocess(
            ['locale'],
            stdout=ipc.PIPE, stderr=ipc.PIPE
        )
        stdout, stderr = child.communicate()
        stdout = stdout.decode('UTF-8').splitlines()
        stderr = stderr.decode('UTF-8').splitlines()
        self.assertEqual(stderr, [])
        data = dict(line.split('=', 1) for line in stdout)
        has_lc_all = has_lc_ctype = has_lang = 0
        for key, value in data.items():
            if key == 'LC_ALL':
                has_lc_all = 1
                self.assertEqual(value, '')
            elif key == 'LC_CTYPE':
                has_lc_ctype = 1
                self.assertEqual(value, 'en_US.UTF-8')
            elif key == 'LANG':
                has_lang = 1
                self.assertEqual(value, '')
            elif key == 'LANGUAGE':
                self.assertEqual(value, '')
            else:
                self.assertEqual(value, '"POSIX"')
        self.assertTrue(has_lc_all)
        self.assertTrue(has_lc_ctype)
        self.assertTrue(has_lang)

    def test_locale_lc_all(self):
        with interim_environ(LC_ALL='en_US.UTF-8'):
            self._test_locale()

    def test_locale_lc_ctype(self):
        with interim_environ(LC_ALL=None, LC_CTYPE='en_US.UTF-8'):
            self._test_locale()

    def test_locale_lang(self):
        with interim_environ(LC_ALL=None, LC_CTYPE=None, LANG='en_US.UTF-8'):
            self._test_locale()


class RequireTestCase(TestCase):
    def test_ok(self):
        ipc.require('cat')

    def test_fail(self):
        prog = 'ocrodjvu-nonexistent'
        with self.assertRaises(OSError) as ecm:
            ipc.require(prog)
        exc_message = f"[Errno {errno.ENOENT}] command not found: {prog!r}"
        self.assertEqual(str(ecm.exception), exc_message)
