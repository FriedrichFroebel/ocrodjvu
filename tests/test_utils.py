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

import sys
import warnings
from ast import literal_eval

from ocrodjvu import utils

from tests.tools import mock, TestCase


class EnhanceImportTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # noinspection PyTypeChecker
        sys.modules['nonexistent'] = None

    def test_debian(self):
        with mock.patch.object(utils, 'IS_DEBIAN', True):
            with self.assertRaises(expected_exception=ImportError) as exception_manager:
                try:
                    # noinspection PyUnresolvedReferences
                    import nonexistent
                except ImportError as exception:
                    utils.enhance_import_error(
                        exception,
                        'PyNonexistent',
                        'python-nonexistent',
                        'https://pynonexistent.example.net/'
                    )
                    raise
                nonexistent.f()  # quieten pyflakes
            self.assertEqual(
                str(exception_manager.exception),
                (
                    'import of nonexistent halted; None in sys.modules; '
                    'please install the python-nonexistent package'
                )
            )

    def test_non_debian(self):
        with mock.patch.object(utils, 'IS_DEBIAN', False):
            with self.assertRaises(expected_exception=ImportError) as exception_manager:
                try:
                    # noinspection PyUnresolvedReferences
                    import nonexistent
                except ImportError as exception:
                    utils.enhance_import_error(
                        exception,
                        'PyNonexistent',
                        'python-nonexistent',
                        'https://pynonexistent.example.net/'
                    )
                    raise
                nonexistent.f()  # quieten pyflakes
            self.assertEqual(
                str(exception_manager.exception),
                (
                    'import of nonexistent halted; None in sys.modules; '
                    'please install the PyNonexistent package <https://pynonexistent.example.net/>'
                )
            )

    def test_without_debian_package_name(self):
        def t():
            with self.assertRaises(expected_exception=ImportError) as exception_manager:
                try:
                    # noinspection PyUnresolvedReferences
                    import nonexistent
                except ImportError as exception:
                    utils.enhance_import_error(
                        exception,
                        'PyNonexistent',
                        None,
                        'https://pynonexistent.example.net/'
                    )
                    raise
                nonexistent.f()  # quieten pyflakes
            self.assertEqual(
                str(exception_manager.exception),
                (
                    'import of nonexistent halted; None in sys.modules; '
                    'please install the PyNonexistent package <https://pynonexistent.example.net/>'
                )
            )

        with mock.patch.object(utils, 'IS_DEBIAN', False):
            t()
        with mock.patch.object(utils, 'IS_DEBIAN', True):
            t()


class SmartReprTestCase(TestCase):
    def test_string(self):
        for s in '', '\f', 'eggs', '''e'gg"s''', 'jeż', '''j'e"ż''':
            self.assertEqual(literal_eval(utils.smart_repr(s)), s)

    def test_encoded_string(self):
        for s in '', '\f', 'eggs', '''e'gg"s''':
            self.assertEqual(literal_eval(utils.smart_repr(s, 'ASCII')), s)
            self.assertEqual(literal_eval(utils.smart_repr(s, 'UTF-8')), s)
        for s in 'jeż', '''j'e"ż''':
            s_repr = utils.smart_repr(s, 'ASCII')
            self.assertIsInstance(s_repr, str)
            self.assertEqual(literal_eval(s_repr), s)
        for s in 'jeż', '''j'e"ż''':
            s_repr = utils.smart_repr(s, 'UTF-8')
            self.assertIsInstance(s_repr, str)
            self.assertIn('ż', s_repr)
            self.assertEqual(literal_eval(s_repr), s)


class ParsePageNumbersTestCase(TestCase):
    def test_none(self):
        self.assertIsNone(utils.parse_page_numbers(None))

    def test_single(self):
        self.assertEqual(utils.parse_page_numbers('17'), [17])

    def test_range(self):
        self.assertEqual(utils.parse_page_numbers('37-42'), [37, 38, 39, 40, 41, 42])

    def test_multiple(self):
        self.assertEqual(utils.parse_page_numbers('17,37-42'), [17, 37, 38, 39, 40, 41, 42])

    def test_bad_range(self):
        self.assertEqual(utils.parse_page_numbers('42-37'), [])

    def test_collapsed_range(self):
        self.assertEqual(utils.parse_page_numbers('17-17'), [17])


class SanitizeUtf8TestCase(TestCase):
    def test_control_characters(self):
        def show(message, category, filename, lineno, file=None, line=None):
            with self.assertRaisesRegex(utils.EncodingWarning, '.*control character.*'):
                raise message

        s = ''.join(map(chr, range(32)))
        s = s.encode('UTF-8')
        with warnings.catch_warnings():
            warnings.showwarning = show
            t = utils.sanitize_utf8(s).decode('UTF-8')
        self.assertEqual(
            t,
            (
                '\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD'
                '\uFFFD\t\n\uFFFD\uFFFD\r\uFFFD\uFFFD'
                '\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD'
                '\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD'
            )
        )

    def test_ascii(self):
        s = b'The quick brown fox jumps over the lazy dog'
        with warnings.catch_warnings():
            warnings.filterwarnings('error', category=utils.EncodingWarning)
            t = utils.sanitize_utf8(s)
        self.assertEqual(s, t)

    def test_utf8(self):
        s = 'Jeżu klątw, spłódź Finom część gry hańb'.encode('UTF-8')
        with warnings.catch_warnings():
            warnings.filterwarnings('error', category=utils.EncodingWarning)
            t = utils.sanitize_utf8(s)
        self.assertEqual(s, t)

    def test_non_utf8(self):
        def show(message, category, filename, lineno, file=None, line=None):
            with self.assertRaisesRegex(utils.EncodingWarning, '.* invalid continuation byte'):
                raise message

        s0 = 'Jeżu klątw, spłódź Finom część gry hańb'.encode('UTF-8')
        good = 'ó'.encode('UTF-8')
        bad = good.decode('UTF-8').encode('ISO-8859-2')
        s1 = s0.replace(good, bad)
        s2 = s0.replace(good, '\N{REPLACEMENT CHARACTER}'.encode('UTF-8'))
        with warnings.catch_warnings():
            warnings.showwarning = show
            t = utils.sanitize_utf8(s1)
        self.assertEqual(s2, t)


class NotOverridenTestCase(TestCase):
    class B:
        @utils.not_overridden
        def f(self, x, y):
            pass

    class C(B):
        def f(self, x, y):
            return x * y

    def test_not_overridden(self):
        def show(message, category, filename, lineno, file=None, line=None):
            with self.assertRaisesRegex(utils.NotOverriddenWarning, r'^.*\bB.f[(][)] is not overridden$'):
                raise message

        with warnings.catch_warnings():
            warnings.showwarning = show
            self.assertIsNone(self.B().f(6, 7))

    def test_overridden(self):
        with warnings.catch_warnings():
            warnings.filterwarnings('error', category=utils.NotOverriddenWarning)
            result = self.C().f(6, 7)
            self.assertEqual(result, 42)


class StrAsUnicodeTestCase(TestCase):
    def test_ascii(self):
        for s in '', 'eggs', u'eggs':
            self.assertEqual(utils.str_as_unicode(s), '' + s)
            self.assertEqual(utils.str_as_unicode(s, 'UTF-8'), '' + s)
            self.assertEqual(utils.str_as_unicode(s, 'ASCII'), '' + s)

    def test_nonascii(self):
        rc = '\N{REPLACEMENT CHARACTER}'
        s = 'jeż'.encode('UTF-8')
        self.assertEqual(utils.str_as_unicode(s, 'ASCII'), 'je' + rc + rc)
        self.assertEqual(utils.str_as_unicode(s, 'UTF-8'), 'jeż')

    def test_unicode(self):
        s = 'jeż'
        self.assertEqual(utils.str_as_unicode(s), s)
        self.assertEqual(utils.str_as_unicode(s, 'ASCII'), s)
        self.assertEqual(utils.str_as_unicode(s, 'UTF-8'), s)


class IdentityTestCase(TestCase):
    def test_identity(self):
        o = object()
        self.assertIs(utils.identity(o), o)


class PropertyTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        class Dummy:
            eggs = utils.Property()
            ham = utils.Property(default_value=42)

        cls.Dummy = Dummy

    def test_class(self):
        eggs = self.Dummy.eggs
        ham = self.Dummy.ham
        for obj in eggs, ham:
            self.assertIsInstance(obj, utils.Property)

    def test_default_filter(self):
        dummy = self.Dummy()
        self.assertIsNone(dummy.eggs)
        self.assertEqual(dummy.ham, 42)
        dummy.eggs = -4
        dummy.ham = -2
        self.assertEqual(dummy.eggs, -4)
        self.assertEqual(dummy.ham, -2)
        dummy = self.Dummy()
        self.assertIsNone(dummy.eggs)
        self.assertEqual(dummy.ham, 42)


class GetCpuCountTestCase(TestCase):
    def test_get_cpu_count(self):
        n = utils.get_cpu_count()
        self.assertIsInstance(n, int)
        self.assertGreaterEqual(n, 1)


class GetThreadLimitTestCase(TestCase):
    def test_get_thread_limit(self):
        for item_count in range(0, 10):
            for job_count in range(1, 10):
                with self.subTest(item_count=item_count, job_count=job_count):
                    limit = utils.get_thread_limit(item_count, job_count)
                    self.assertIsInstance(limit, int)
                    if item_count == 0:
                        self.assertEqual(limit, 1)
                    else:
                        npitems = min(item_count, job_count)
                        self.assertLessEqual(limit * npitems, job_count)
                        self.assertGreater((limit + 1) * npitems, job_count)
