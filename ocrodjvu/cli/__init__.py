# Copyright © 2011-2022 Jakub Wilk <jwilk@jwilk.net>
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

from ocrodjvu import errors


class ArgumentParser(argparse.ArgumentParser):

    def exit(self, status=0, message=None):
        if status:
            status = errors.EXIT_FATAL
        argparse.ArgumentParser.exit(self, status=status, message=message)
