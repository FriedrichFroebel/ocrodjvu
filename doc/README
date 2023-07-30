Overview
========

**ocrodjvu** is a wrapper for OCR systems that allows you to perform OCR on DjVu_ files.

.. _DjVu:
   http://djvu.org/

Example
-------

.. code:: console

   $ wget -q 'https://sources.debian.org/data/main/o/ocropus/0.3.1-3/data/pages/alice_1.png'
   $ gm convert -threshold 50% 'alice_1.png' 'alice.pbm'
   $ cjb2 'alice.pbm' 'alice.djvu'
   $ ocrodjvu --in-place 'alice.djvu'
   Processing 'alice.djvu':
   - Page #1
   $ djvused -e print-txt 'alice.djvu'
   (page 0 0 2488 3507
    (column 470 2922 1383 2978
     (para 470 2922 1383 2978
      (line 470 2922 1383 2978
       (word 470 2927 499 2976 "1")
       (word 588 2926 787 2978 "Down")
       (word 817 2925 927 2977 "the")
       (word 959 2922 1383 2976 "Rabbit-Hole"))))
    (column 451 707 2076 2856
     (para 463 2626 2076 2856
      (line 465 2803 2073 2856
       (word 465 2819 569 2856 "Alice")
       (word 592 2819 667 2841 "was")
       (word 690 2808 896 2854 "beginning")
   ⋮

Requisites
==========

The following software is required to run ocrodjvu:

* Python_ 3

* an OCR engine:

  + Cuneiform_ ≥ 0.7
  + Ocrad_ ≥ 0.10
  + GOCR_ ≥ 0.40
  + Tesseract_ ≥ 2.00

* DjVuLibre_ ≥ 3.5.21 (≥ 3.5.26 for latest python-djvulibre)

* python-djvulibre_ ≥ 0.4

  + Please note that installing this package currently is a bit more complicated since Cython 3 has been relased on 2023-07-17.
  + While `Issue #11`_ is unresolved, PyPI releases require some workarounds (installing the package from the source archive with the deprecated ``python setup.py install`` beforehand).
  + Alternative: Install the latest package version from `Git <python-djvulibre-git_>`_.

* lxml_ ≥ 2.0

Additionally, some optional features require the following software:

* PyICU_ ≥ 1.0.1 —
  required for the ``--word-segmentation=uax29`` option

* html5lib_ —
  required for the ``--html5`` option

The following software is required to rebuild the manual pages from source:

* xsltproc_

* `DocBook XSL stylesheets`_


.. _Python:
   https://www.python.org/
.. _Cuneiform:
   https://launchpad.net/cuneiform-linux
.. _Ocrad:
   https://www.gnu.org/software/ocrad/
.. _GOCR:
   https://www-e.uni-magdeburg.de/jschulen/ocr/
.. _Tesseract:
   https://github.com/tesseract-ocr/tesseract
.. _DjVuLibre:
   http://djvu.sourceforge.net/
.. _python-djvulibre:
   https://jwilk.net/software/python-djvulibre
.. _Issue #11:
   https://github.com/FriedrichFroebel/python-djvulibre/issues/11
.. _python-djvulibre-git:
   https://github.com/FriedrichFroebel/python-djvulibre
.. _lxml:
   https://lxml.de/
.. _PyICU:
   https://pypi.org/project/PyICU/
.. _html5lib:
   https://github.com/html5lib/html5lib-python
.. _xsltproc:
   http://xmlsoft.org/XSLT/xsltproc2.html
.. _DocBook XSL stylesheets:
   https://github.com/docbook/xslt10-stylesheets

Installation
============

The easiest way to install ocrodjvu is from PyPI::

    pip install ocrodjvu

Alternatively, you can use ocrodjvu without installing it, straight out of an unpacked source tarball or a VCS checkout.

It's also possible to install it from source for the current interpreter with::

   pip install .

The man pages can be deployed using::

   make install_manpage

By default, ``make install_manpage`` installs them to ``/usr/local/``. You can specify a different installation prefix by setting the ``PREFIX`` variable, e.g.::

   make install PREFIX="$HOME/.local"

About this fork
===============

This repository is a port of the original repository to Python 3.

The process involved the *2to3* tool and manual fixes afterwards to get the existing tests to pass. While this port started from scratch to already include the latest upstream changes, the fork by `@rmast`_ which accumulated previous porting attempts provided some great help (see `Issue #39`_ as well).

Due to the upstream repository having been archived (`Issue #46`_), this fork will now be maintained on its own. Please note that I do not have any plans on implementing completely new features for now. Nevertheless, I am going to try to keep this fork working for at least the parts which I actually use on a regular basis.

Differences from upstream
-------------------------

* Package requires Python ≥ 3.6.
* Migrate from *nose* to plain *unittest* stdlib module.
* Conform to PEP8 coding style.
* Use standardized *setup.py*-based installation.
* Rename *lib* to *ocrodjvu* and migrate *ocrodjvu* binary to *__main__.py* and console script version.
* Drop support for *ocropus*/*ocropy* as only the rather old legacy versions ≤ 0.3.1 from 2008 have been supported.


.. _@rmast:
   https://github.com/rmast/ocrodjvu/tree/python3
.. _Issue #46:
   https://github.com/jwilk-archive/ocrodjvu/issues/46
.. _Issue #39:
   https://github.com/jwilk-archive/ocrodjvu/issues/39

Acknowledgment
==============

ocrodjvu development was supported by the Polish Ministry of Science
and Higher Education's grant no. N N519 384036 (2009–2012,
https://bitbucket.org/jsbien/ndt).
