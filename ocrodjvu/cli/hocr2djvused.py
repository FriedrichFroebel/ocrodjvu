# Copyright © 2008-2017 Jakub Wilk <jwilk@jwilk.net>
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

from ocrodjvu import cli
from ocrodjvu import hocr
from ocrodjvu import text_zones
from ocrodjvu import version


__version__ = version.__version__


class ArgumentParser(cli.ArgumentParser):

    _details_map = dict(
        lines=hocr.TEXT_DETAILS_LINE,
        words=hocr.TEXT_DETAILS_WORD,
        chars=hocr.TEXT_DETAILS_CHARACTER,
    )

    def __init__(self):
        cli.ArgumentParser.__init__(self)
        self.add_argument('--version', action=version.VersionAction)
        self.add_argument('--rotation', dest='rotation', action='store', type=int, default=0, help='page rotation (in degrees)')

        def size(s):
            return list(map(int, s.split('x', 1)))

        self.add_argument(
            '--page-size', metavar='WxH', dest='page_size', action='store', type=size, default=None, help='page size (in pixels)'
        )
        group = self.add_argument_group(title='word segmentation options')
        group.add_argument(
            '-t', '--details', dest='details', choices=('lines', 'words', 'chars'), action='store', default='words',
            help='amount of text details to extract'
        )
        group.add_argument(
            '--word-segmentation', dest='word_segmentation', choices=('simple', 'uax29'), default='simple',
            help='word segmentation algorithm'
        )
        # -l/--language is currently not very useful, as ICU does not have any specialisations for languages ocrodjvu supports:
        group.add_argument('-l', '--language', dest='language', help=argparse.SUPPRESS or 'language for word segmentation', default='eng')
        self.add_argument('--html5', dest='html5', action='store_true', help='use HTML5 parser')
        self.add_argument('--fix-utf8', dest='fix_utf8', action='store_true', help='attempt to fix UTF-8 encoding issues')
        self.add_argument(
            'input_files', metavar='FILE', nargs='*', type=argparse.FileType('r'), default=[sys.stdin],
            help='hOCR file to parse (default: standard input)'
        )

    def parse_args(self, args=None, namespace=None):
        options = cli.ArgumentParser.parse_args(self, args, namespace)
        if options.rotation % 90 != 0:
            self.error('rotation must be a multiple of 90 degrees')
        options.details = self._details_map[options.details]
        options.uax29 = options.language if options.word_segmentation == 'uax29' else None
        del options.word_segmentation
        return options


def get_texts(options):
    for input_file in options.input_files:
        texts = hocr.extract_text(
            input_file,
            rotation=options.rotation,
            details=options.details,
            uax29=options.uax29,
            html5=options.html5,
            fix_utf8=options.fix_utf8,
            page_size=options.page_size,
        )
        for text in texts:
            yield text


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    options = ArgumentParser().parse_args(argv[1:])
    for i, text in enumerate(get_texts(options)):
        sys.stdout.write(f'select {i + 1}\nremove-txt\nset-txt\n')
        text_zones.print_sexpr(text, sys.stdout, width=80)
        sys.stdout.write('\n.\n\n')
