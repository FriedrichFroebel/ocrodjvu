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

from ocrodjvu.unicode_support import get_icu, simple_word_break_iterator, word_break_iterator

from tests.tools import TestCase


TEXT = '\u201CJekyll,\u201D cried Utterson, with a\xa0loud voice, \u201CI demand to see you.\u201D'


class SimpleWordBreakIteratorTestCase(TestCase):
    def test_non_empty(self):
        t = list(simple_word_break_iterator(TEXT))
        s = [9, 10, 15, 16, 25, 26, 30, 31, 32, 33, 37, 38, 44, 45, 47, 48, 54, 55, 57, 58, 61, 62, 67]
        self.assertEqual(t, s)
        self.assertEqual(s[-1], len(TEXT))

    def test_empty(self):
        t = list(simple_word_break_iterator(''))
        self.assertEqual(t, [])


class WordBreakIteratorTestCase(TestCase):
    def test_nolocale(self):
        t = list(word_break_iterator(TEXT))
        s = [9, 10, 15, 16, 25, 26, 30, 31, 32, 33, 37, 38, 44, 45, 47, 48, 54, 55, 57, 58, 61, 62, 67]
        self.assertEqual(t, s)
        self.assertEqual(s[-1], len(TEXT))

    def test_nolocale_empty(self):
        t = list(word_break_iterator(''))
        self.assertEqual(t, [])

    def test_en(self):
        icu = get_icu()
        self.assertIsNotNone(icu)
        t = list(word_break_iterator(TEXT, icu.Locale('en')))
        s = [1, 7, 8, 9, 10, 15, 16, 24, 25, 26, 30, 31, 32, 33, 37, 38, 43, 44, 45, 46, 47, 48, 54, 55, 57, 58, 61, 62, 65, 66, 67]
        self.assertEqual(t, s)
        self.assertEqual(s[-1], len(TEXT))

    def test_en_simple(self):
        # Trigger reference-counting bug that was fixed in PyICU 1.0.1:
        # https://github.com/ovalhub/pyicu/commit/515e076682e29d806aeb5f6b1016b799d03d92a9
        icu = get_icu()
        self.assertIsNotNone(icu)
        t = list(word_break_iterator('eggs', icu.Locale('en')))
        self.assertEqual(t, [4])

    def test_en_empty(self):
        icu = get_icu()
        self.assertIsNotNone(icu)
        t = list(word_break_iterator('', icu.Locale('en')))
        self.assertEqual(t, [])
