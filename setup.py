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

from setuptools import setup, find_packages
from pathlib import Path


ROOT_DIRECTORY = Path(__file__).parent.resolve()


def get_version():
    changelog = ROOT_DIRECTORY / 'doc' / 'changelog'
    with open(changelog, mode='r') as fd:
        line = fd.readline()
    return line.split()[1].strip('()')


setup(
    name='ocrodjvu',
    description='OCR for DjVu (Python 3 fork)',
    version=get_version(),
    license='GNU GPL 2',
    long_description=(ROOT_DIRECTORY / 'README.rst').read_text(encoding='utf-8'),
    long_description_content_type='text/x-rst',
    author='Jakub Wilk, FriedrichFröbel (Python 3)',
    url='https://github.com/FriedrichFroebel/ocrodjvu/',
    packages=find_packages(
        where='.',
        exclude=['tests', 'tests.*', 'private', 'private.*']
    ),
    include_package_data=True,
    python_requires=">=3.6, <4",
    install_requires=[
        'python-djvulibre>=0.4',
        'lxml>=2.0',
    ],
    extras_require={
        'dev': [
            'coverage',
            'flake8',
            'pep8-naming',
            'Pillow',
        ],
        'docs': [
            'docutils',
            'pygments',
        ]
    },
    entry_points={
        'console_scripts': [
            'ocrodjvu=ocrodjvu.__main__:ocrodjvu_main',
            'djvu2hocr=ocrodjvu.__main__:djvu2hocr_main',
            'hocr2djvused=ocrodjvu.__main__:hocr2djvused_main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Text Processing',
        'Topic :: Multimedia :: Graphics',
    ]
)
