# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
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

import io

from ocrodjvu import text_zones

from tests.tools import TestCase


class PrintSexprTestCase(TestCase):
    def test_print_sexpr(self):
        inp = 'jeż'
        out = '"jeż"'
        fp = io.StringIO()
        expr = text_zones.sexpr.Expression(inp)
        text_zones.print_sexpr(expr, fp)
        fp.seek(0)
        self.assertEqual(fp.getvalue(), out)
