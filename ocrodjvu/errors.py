# Copyright © 2009-2019 Jakub Wilk <jwilk@jwilk.net>
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


class UnknownLanguageListError(Exception):

    def __init__(self):
        Exception.__init__(self, 'unable to determine list of available languages')


class InvalidLanguageIdError(ValueError):

    def __init__(self, name):
        ValueError.__init__(
            self,
            f'invalid language identifier: {name}; language identifier is typically an ISO 639-2 three-letter code'
        )


class MissingLanguagePackError(Exception):

    def __init__(self, language):
        Exception.__init__(self, f'language pack for the selected language ({language}) is not available')


class EngineNotFoundError(Exception):

    def __init__(self, name):
        Exception.__init__(self, f'OCR engine ({name}) was not found')


class MalformedOcrOutputError(Exception):

    def __init__(self, message):
        Exception.__init__(self, f'malformed OCR output: {message}')


class MalformedHocrError(MalformedOcrOutputError):

    def __init__(self, message):
        Exception.__init__(self, f'malformed hOCR document: {message}')


EXIT_FATAL = 1
EXIT_NONFATAL = 2


def fatal(message):
    ap = argparse.ArgumentParser()
    message = f'{ap.prog}: error: {message}'
    print(message, file=sys.stderr)
    sys.exit(EXIT_FATAL)


__all__ = [
    'UnknownLanguageListError',
    'InvalidLanguageIdError',
    'MissingLanguagePackError',
    'EngineNotFoundError',
    'MalformedOcrOutputError',
    'MalformedHocrError',
    'EXIT_FATAL',
    'EXIT_NONFATAL',
    'fatal',
]
