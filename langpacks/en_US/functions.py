# -*- coding: utf-8 -*-

# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

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

# This file contains language specific program code for English (US)

WCHARS = u"abcdefghijklmnopqrstuvwxyzszèéABCDEFGHIJKLMNOPQRSTUVWXYZÈÉ'"
# Checks if string looks like a valid word. This is a mandatory function.
def checkword(string):
	for c in string:
		if not c in WCHARS: return False
	return True



# Lists the language specific output types. This is a mandatory function.
def jooutput_list_supported_types():
	types = []
	return types

# Language specific list output. This is a mandatory function.
def jooutput_call(req, outputtype, db, query):
	joheaders.error_page(req, _(u'Unsupported output type'))
