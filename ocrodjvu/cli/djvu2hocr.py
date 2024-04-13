# Copyright © 2009-2022 Jakub Wilk <jwilk@jwilk.net>
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
import html
import locale
import os
import re
import sys

from ocrodjvu import cli
from ocrodjvu import hocr
from ocrodjvu import ipc
from ocrodjvu import logger
from ocrodjvu import temporary
from ocrodjvu import text_zones
from ocrodjvu import unicode_support
from ocrodjvu import utils
from ocrodjvu import version

from ocrodjvu.hocr import etree
from ocrodjvu.text_zones import const, sexpr


__version__ = version.__version__

SYSTEM_ENCODING = locale.getpreferredencoding()

LOGGER = logger.setup()


class ArgumentParser(cli.ArgumentParser):

    def __init__(self):
        usage = '%(prog)s [options] FILE'
        cli.ArgumentParser.__init__(self, usage=usage)
        self.add_argument('--version', action=version.VersionAction)
        group = self.add_argument_group(title='input selection options')
        group.add_argument('path', metavar='FILE', help='DjVu file to covert')

        def pages(x):
            return utils.parse_page_numbers(x)

        group.add_argument('-p', '--pages', dest='pages', action='store', default=None, type=pages, help='pages to convert')
        group = self.add_argument_group(title='word segmentation options')
        group.add_argument(
            '--word-segmentation', dest='word_segmentation', choices=('simple', 'uax29'), default='simple',
            help='word segmentation algorithm'
        )
        # -l/--language is currently not very useful, as ICU does not have any specialisations for languages ocrodjvu supports:
        group.add_argument('-l', '--language', dest='language', help=argparse.SUPPRESS or 'language for word segmentation', default='eng')
        group = self.add_argument_group(title='HTML output options')
        group.add_argument('--title', dest='title', help='document title', default='DjVu hidden text layer')
        group.add_argument('--css', metavar='STYLE', dest='css', help='CSS style', default='')

    def parse_args(self, args=None, namespace=None):
        options = cli.ArgumentParser.parse_args(self, args, namespace)
        if options.word_segmentation == 'uax29':
            options.icu = icu = unicode_support.get_icu()
            options.locale = icu.Locale(options.language)
        else:
            options.icu = None
            options.locale = None
        return options


class CharacterLevelDetailsError(Exception):
    pass


class Zone:

    def __init__(self, sexpr_, page_height):
        self._sexpr = sexpr_
        self._page_height = page_height

    @property
    def type(self):
        return const.get_text_zone_type(self._sexpr[0].value)

    @property
    def bbox(self):
        return text_zones.BBox(
            self._sexpr[1].value,
            self._page_height - self._sexpr[4].value,
            self._sexpr[3].value,
            self._page_height - self._sexpr[2].value,
        )

    @property
    def text(self):
        if len(self._sexpr) != 6:
            raise TypeError(f'list of {len(self._sexpr)} (!= 6) elements')  # no coverage
        if not isinstance(self._sexpr[5], sexpr.StringExpression):
            raise TypeError('last element is not a string')  # no coverage
        return self._sexpr[5].value

    @property
    def children(self):
        for child in self._sexpr[5:]:
            if isinstance(child, sexpr.ListExpression):
                yield Zone(child, self._page_height)
            else:
                yield self.text
                return

    @property
    def n_children(self):
        n = len(self._sexpr) - 5
        if n <= 0:
            raise TypeError(f'list of {len(self._sexpr)} (< 6) elements')  # no coverage
        return n

    def __repr__(self):
        return f'{type(self).__name__}({self._sexpr!r})'


_XML_STRING_RE = re.compile(
    '''
    ([^\x00-\x08\x0B\x0C\x0E-\x1F]*)
    ( [\x00-\x08\x0B\x0C\x0E-\x1F]?)
    ''',
    re.VERBOSE
)


def set_text(element, text):
    last = None
    for match in _XML_STRING_RE.finditer(text):
        if match.group(1):
            if last is None:
                element.text = match.group(1)
            else:
                last.tail = match.group(1)
        if match.group(2):
            last = etree.Element('span')
            last.set('class', 'djvu_char')
            last.set('title', f'#x{ord(match.group(2)):02x}')
            last.text = ' '
            element.append(last)


def break_chars(char_zone_list, options):
    bbox_list = []
    text = []
    for char_zone in char_zone_list:
        bbox = char_zone.bbox
        char_text = char_zone.text
        if not char_text:
            continue
        for i, char in enumerate(char_text):
            subbox = text_zones.BBox(
                int(bbox.x0 + (bbox.x1 - bbox.x0) * 1.0 * i / len(char_text) + 0.5),
                bbox.y0,
                int(bbox.x0 + (bbox.x1 - bbox.x0) * 1.0 * (i + 1) / len(char_text) + 0.5),
                bbox.y1,
            )
            bbox_list += [subbox]
        text += [char_text]
    text = ''.join(text)
    break_iterator = unicode_support.word_break_iterator(text, options.locale)
    element = None
    i = 0
    for j in break_iterator:
        subtext = text[i:j]
        if subtext.isspace():
            if element is not None:
                element.tail = ' '
            i = j
            continue
        bbox = text_zones.BBox()
        for k in range(i, j):
            bbox.update(bbox_list[k])
        element = etree.Element('span')
        element.set('class', 'ocrx_word')
        element.set('title', 'bbox {bbox}; bboxes {bboxes}'.format(
            bbox=' '.join(map(str, bbox)),
            bboxes=', '.join(' '.join(map(str, bbox)) for bbox in bbox_list[i:j])
        ))
        set_text(element, subtext)
        yield element
        i = j


def break_plain_text(text, bbox, options):
    break_iterator = unicode_support.word_break_iterator(text, options.locale)
    i = 0
    element = None
    for j in break_iterator:
        subtext = text[i:j]
        if subtext.isspace():
            if element is not None:
                element.tail = ' '
            i = j
            continue
        subbox = text_zones.BBox(
            int(bbox.x0 + (bbox.x1 - bbox.x0) * 1.0 * i / len(text) + 0.5),
            bbox.y0,
            int(bbox.x0 + (bbox.x1 - bbox.x0) * 1.0 * j / len(text) + 0.5),
            bbox.y1,
        )
        element = etree.Element('span')
        element.set('class', 'ocrx_word')
        element.set('title', 'bbox ' + ' '.join(map(str, subbox)))
        set_text(element, subtext)
        yield element
        i = j


def process_zone(parent, zone, last, options):
    zone_type = zone.type
    if zone_type <= const.TEXT_ZONE_LINE and parent is not None:
        parent.tail = '\n'
    try:
        hocr_tag, hocr_class = hocr.DJVU_ZONE_TO_HOCR(zone_type)
    except LookupError as ex:
        if ex.args[0] == const.TEXT_ZONE_CHARACTER:
            raise CharacterLevelDetailsError()
        raise
    self = etree.Element(hocr_tag)
    self.set('class', hocr_class)
    if zone_type == const.TEXT_ZONE_PAGE:
        bbox = options.page_bbox
    else:
        bbox = zone.bbox
    self.set('title', 'bbox ' + ' '.join(map(str, bbox)))
    n_children = zone.n_children
    character_level_details = False
    for n, child_zone in enumerate(zone.children):
        last_child = n == n_children - 1
        if isinstance(child_zone, Zone):
            try:
                process_zone(self, child_zone, last=last_child, options=options)
            except CharacterLevelDetailsError:
                # Do word segmentation by hand.
                character_level_details = True
                break
    if character_level_details:
        # Do word segmentation by hand.
        child = None
        for child in break_chars(zone.children, options):
            parent.append(child)
        if child is not None and zone_type == const.TEXT_ZONE_WORD and not last:
            child.tail = ' '
        self = None
    elif isinstance(child_zone, str):
        text = child_zone
        if zone_type >= const.TEXT_ZONE_WORD and options.icu is not None and parent is not None:
            # Do word segmentation by hand.
            child = None
            for child in break_plain_text(text, bbox, options):
                parent.append(child)
            if child is not None and zone_type == const.TEXT_ZONE_WORD and not last:
                child.tail = ' '
            self = None
        else:
            # Word segmentation as provided by DjVu.
            # There's no point in doing word segmentation if only line coordinates are provided.
            set_text(self, text)
            if zone_type == const.TEXT_ZONE_WORD and not last:
                self.tail = ' '
    if parent is not None and self is not None:
        parent.append(self)
    return self


def process_page(page_text, options):
    result = process_zone(None, page_text, last=True, options=options)
    tree = etree.ElementTree(result)
    sys.stdout.write(etree.tostring(tree, encoding='UTF-8', method='xml').decode('UTF-8'))


HOCR_HEADER_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="ocr-system" content="{ocr_system}" />
  <meta name="ocr-capabilities" content="{ocr_capabilities}" />
  <style type="text/css">{css}</style>
  <title>{title}</title>
</head>
<body>
'''

HOCR_HEADER_STYLE_RE = re.compile(r'^\s+<style\s.*?\n', re.MULTILINE)

HOCR_FOOTER = '''
</body>
</html>
'''


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    options = ArgumentParser().parse_args(argv[1:])
    LOGGER.info(f'Converting {options.path}:')
    if options.pages is None:
        with ipc.Subprocess(
                ['djvused', '-e', 'n', os.path.abspath(options.path)],
                stdout=ipc.PIPE,
        ) as djvused:
            n_pages = int(djvused.stdout.readline())
        options.pages = range(1, n_pages + 1)
    page_iterator = iter(options.pages)
    sed_script = temporary.file(suffix='.djvused', mode='w+', encoding='UTF-8')
    for n in options.pages:
        print(f'select {n}; size; print-txt', file=sed_script)
    sed_script.flush()
    with ipc.Subprocess(
            ['djvused', '-f', sed_script.name, os.path.abspath(options.path)],
            stdout=ipc.PIPE,
    ) as djvused:
        ocr_system = f'djvu2hocr {__version__}'
        hocr_header = HOCR_HEADER_TEMPLATE.format(
            ocr_system=ocr_system,
            ocr_capabilities=' '.join(hocr.DJVU2HOCR_CAPABILITIES),
            title=html.escape(options.title),
            css=html.escape(options.css),
        )
        if not options.css:
            hocr_header = re.sub(HOCR_HEADER_STYLE_RE, '', hocr_header, count=1)
        sys.stdout.write(hocr_header)
        for n in page_iterator:
            try:
                page_size = [
                    int(str(sexpr.Expression.from_stream(djvused.stdout).value).split('=')[1])
                    for _ in range(2)
                ]
                options.page_bbox = text_zones.BBox(0, 0, page_size[0], page_size[1])
                page_text = sexpr.Expression.from_stream(djvused.stdout)
            except sexpr.ExpressionSyntaxError:
                break
            LOGGER.info(f'- Page #{n}')
            page_zone = Zone(page_text, page_size[1])
            process_page(page_zone, options)
        sys.stdout.write(HOCR_FOOTER)
