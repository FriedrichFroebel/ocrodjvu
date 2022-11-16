# encoding=UTF-8

# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
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

import io

from tests.tools import TestCase

from lib import text_zones


class PrintSexprTestCase(TestCase):
    def test_print_sexpr(self):
        inp = 'jeż'
        out = '"jeż"'
        fp = io.StringIO()
        expr = text_zones.sexpr.Expression(inp)
        text_zones.print_sexpr(expr, fp)
        fp.seek(0)
        self.assertEqual(fp.getvalue(), out)

# vim:ts=4 sts=4 sw=4 et
