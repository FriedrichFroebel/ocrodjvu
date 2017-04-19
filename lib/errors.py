# encoding=UTF-8

# Copyright © 2009-2015 Jakub Wilk <jwilk@jwilk.net>
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

class UnknownLanguageList(Exception):

    def __init__(self):
        Exception.__init__(self,
            'unable to determine list of available languages'
        )

class InvalidLanguageId(ValueError):

    def __init__(self, name):
        ValueError.__init__(self,
            'invalid language identifier: {lang}; '
            'language identifier is typically an ISO 639-2 three-letter code'
            .format(lang=name)
        )

class MissingLanguagePack(Exception):

    def __init__(self, language):
        Exception.__init__(self,
            'language pack for the selected language ({lang}) is not available'
            .format(lang=language)
        )

class EngineNotFound(Exception):

    def __init__(self, name):
        Exception.__init__(self,
            'OCR engine ({engine}) was not found'
            .format(engine=name)
        )

class MalformedOcrOutput(Exception):

    def __init__(self, message):
        Exception.__init__(self,
            'malformed OCR output: {msg}'
            .format(msg=message)
        )

class MalformedHocr(MalformedOcrOutput):

    def __init__(self, message):
        Exception.__init__(self,
            'malformed hOCR document: {msg}'
            .format(msg=message)
        )

EXIT_FATAL = 1
EXIT_NONFATAL = 2

# vim:ts=4 sts=4 sw=4 et
