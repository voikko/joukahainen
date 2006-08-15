# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Makefile for updating the translations etc.

SOURCES_TO_TRANSLATE := wwwroot/word.py wwwroot/user.py wwwroot/_apply_config.py \
	pylib/jotools.py pylib/joeditors.py
POTFILE := transl/joukahainen.pot


LINGUAS := $(patsubst langpacks/%/messages.po,%,$(wildcard langpacks/*/messages.po))
POFILES := $(patsubst %,transl/%.po,$(LINGUAS))
MOFILES := $(patsubst %,transl/%/LC_MESSAGES/joukahainen.mo,$(LINGUAS))

.PHONY: all

all: $(POTFILE) $(POFILES) $(MOFILES)

$(POTFILE): $(SOURCES_TO_TRANSLATE)
	mkdir -p transl
	xgettext -L Python -d joukahainen -o $@ $(SOURCES_TO_TRANSLATE)


# Rule for merging translations
transl/%.po: langpacks/%/messages.po $(POTFILE)
	msgmerge -o $@ $< $(POTFILE)

# Rule for creating .mo files
transl/%/LC_MESSAGES/joukahainen.mo: transl/%.po
	mkdir -p $(@D)
	msgfmt -o $@ $<

