#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
