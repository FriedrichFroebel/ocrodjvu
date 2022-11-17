# encoding=UTF-8

# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
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
import os

from PIL import Image

import djvu.decode

from ocrodjvu import image_io

from tests.tools import sorted_glob, TestCase


class ImageIoTestCase(TestCase):
    here = os.path.dirname(__file__)
    here = os.path.relpath(here)

    formats = image_io.PNM, image_io.BMP, image_io.TIFF

    def _test_from_file(self, base_filename, image_format):
        if image_format.bpp == 1:
            layers = djvu.decode.RENDER_MASK_ONLY
        else:
            layers = djvu.decode.RENDER_COLOR
        base_filename = os.path.join(self.here, base_filename)
        djvu_filename = f'{base_filename}.djvu'
        expected_filename = f'{base_filename}_{image_format.bpp}bpp.{image_format.extension}'
        with open(expected_filename, 'rb') as fd:
            expected = fd.read()
        context = djvu.decode.Context()
        document = context.new_document(djvu.decode.FileUri(djvu_filename))
        page_job = document.pages[0].decode(wait=True)
        fd = io.BytesIO()
        image_format.write_image(page_job, layers, fd)
        result = fd.getvalue()
        self.assertEqual(len(result), len(expected))
        if result == expected:
            # The easy part:
            return
        else:
            # The result might be still correct, even if the strings are different.
            # Think of BMP format and its padding bytes.
            with Image.open(expected_filename) as expected, Image.open(io.BytesIO(result)) as result:
                self.assertEqual(result.format, expected.format)
                self.assertEqual(result.size, expected.size)
                self.assertEqual(result.mode, expected.mode)
                if result.palette is None:
                    self.assertIsNone(expected.palette)
                else:
                    self.assertEqual(list(result.palette.getdata()), list(expected.palette.getdata()))
                self.assertEqual(list(result.getdata()), list(expected.getdata()))

    def test_from_file(self):
        for djvu_filename in sorted_glob(os.path.join(self.here, '*.djvu')):
            base_filename = os.path.basename(djvu_filename[:-5])
            for image_format in self.formats:
                for bits_per_pixel in 1, 24:
                    with self.subTest(base_filename=base_filename, image_format=image_format, bpp=bits_per_pixel):
                        self._test_from_file(base_filename=base_filename, image_format=image_format(bits_per_pixel))

# vim:ts=4 sts=4 sw=4 et
