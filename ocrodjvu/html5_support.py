# Copyright © 2011-2015 Jakub Wilk <jwilk@jwilk.net>
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

from ocrodjvu import utils


def parse(stream):
    try:
        # Support is optional.
        # noinspection PyPackageRequirements
        import html5lib
    except ImportError as ex:  # no coverage
        utils.enhance_import_error(ex, 'html5lib', 'python-html5lib', 'https://github.com/html5lib/html5lib-python')
        raise
    return html5lib.parse(
        stream,
        treebuilder='lxml',
        namespaceHTMLElements=False
    )
