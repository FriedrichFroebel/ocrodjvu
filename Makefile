# Copyright © 2012-2019 Jakub Wilk <jwilk@jwilk.net>
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

PYTHON = python3

PREFIX = /usr/local
DESTDIR =

mandir = $(PREFIX)/share/man

.PHONY: all
all: ;

.PHONY: install_manpage
install_manpage:
	$(MAKE) -C doc  # build documentation
	install -d $(DESTDIR)$(mandir)/man1
	install -m644 doc/*.1 $(DESTDIR)$(mandir)/man1/

# FIXME: Fix broken `ipc.Subprocess.wait`.
.PHONY: test
test:
	$(PYTHON) -W ignore:ResourceWarning -m unittest discover --start-directory tests/

# FIXME: Fix broken `ipc.Subprocess.wait`.
.PHONY: update-coverage
update-coverage:
	coverage erase
	$(PYTHON) -W ignore:ResourceWarning -m coverage run -m unittest discover --start-directory tests/
	coverage report --include=ocrodjvu/*

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -f .coverage
	rm -f *.tmp

.error = GNU make is required

# vim:ts=4 sts=4 sw=4 noet
