# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
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

import pkgutil


def get_engines():
    for importer, name, is_pkg in pkgutil.iter_modules(__path__):
        this_module = __import__('', globals=globals(), fromlist=(name,), level=1)
        engine = getattr(this_module, name).Engine
        if engine.name is None:
            continue
        yield engine
