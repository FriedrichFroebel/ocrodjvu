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


def ocrodjvu_main():
    from ocrodjvu.cli import ocrodjvu
    ocrodjvu.main()


def djvu2hocr_main():
    from ocrodjvu.cli import djvu2hocr
    djvu2hocr.main()


def hocr2djvused_main():
    from ocrodjvu.cli import hocr2djvused
    hocr2djvused.main()


if __name__ == '__main__':
    ocrodjvu_main()
