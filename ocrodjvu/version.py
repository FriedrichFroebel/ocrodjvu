# Copyright © 2016-2019 Jakub Wilk <jwilk@jwilk.net>
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

import argparse
import sys

__version__ = '0.13.2'


class VersionAction(argparse.Action):
    """
    argparse --version action
    """

    def __init__(self, option_strings, dest=argparse.SUPPRESS):
        super(VersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            help="show program's version information and exit"
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print(f'{parser.prog} {__version__}')
        print('+ Python {0}.{1}.{2}'.format(*sys.version_info))
        try:
            djvu_decode = sys.modules['djvu.decode']
        except LookupError:  # no coverage
            pass
        else:
            print(f'+ python-djvulibre {djvu_decode.__version__}')
        try:
            lxml_etree = sys.modules['lxml.etree']
        except LookupError:  # no coverage
            pass
        else:
            print(f'+ lxml {lxml_etree.__version__}')
        try:
            # noinspection PyPackageRequirements,PyUnresolvedReferences
            import html5lib
        except ImportError:  # no coverage
            pass
        else:
            print(f'+ html5lib-python {html5lib.__version__}')
        try:
            # noinspection PyUnresolvedReferences
            from ocrodjvu import unicode_support
            pyicu = unicode_support.get_icu()
        except ImportError:  # no coverage
            pass
        else:
            print(f'+ PyICU {pyicu.VERSION}')
            print(f'  + ICU {pyicu.ICU_VERSION}')
            print(f'    + Unicode {pyicu.UNICODE_VERSION}')
        parser.exit()


__all__ = [
    'VersionAction',
    '__version__',
]
