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

import io

from ocrodjvu import utils
from ocrodjvu import image_io


class Engine:
    name = None
    image_format = None
    needs_utf8_fix = False
    default_language = 'eng'

    def __init__(self, *args, **kwargs):
        type_name = f'{self.__module__}.{type(self).__name__}'
        if args:
            raise ValueError(f'{type_name}.__init__() takes no positional arguments')  # no coverage
        if not isinstance(self.name, str):
            raise TypeError(f'{type_name}.name must be a string')  # no coverage
        if not issubclass(self.image_format, image_io.ImageFormat):
            raise TypeError(f'{type_name}.image_format must be an ImageFormat subclass')  # no coverage
        for key, value in kwargs.items():
            try:
                prop = getattr(type(self), key)
                if not isinstance(prop, utils.Property):
                    raise AttributeError
            except AttributeError as ex:
                ex.args = (f'{key!r} is not a valid property for the {self.name} engine',)
                raise
            setattr(self, key, value)


class Output:
    format = None

    def __init__(self, contents, format_=None):
        self._contents = contents
        if format_ is not None:
            self.format = format_
        if self.format is None:
            raise TypeError('output format is not defined')

    def __str__(self):
        return self._contents

    def __bytes__(self):
        return self._contents

    def as_stringio(self):
        return io.StringIO(str(self))

    def as_bytesio(self):
        return io.BytesIO(bytes(self))
