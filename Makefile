# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Makefile for updating the translations etc.

SOURCES_TO_TRANSLATE := wwwroot/word.py wwwroot/user.py wwwroot/task.py wwwroot/query.py \
	pylib/_apply_config.py pylib/jooutput.py \
	pylib/jotools.py pylib/joeditors.py pylib/joindex.py pylib/joheaders.py
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

