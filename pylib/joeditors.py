# -*- coding: utf-8 -*-

# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
# This file is part of Joukahainen, a vocabulary management application

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

# This file contains metadata display and editor components

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return "Error: word class %i does not exists" % classid
	return ("<span class=\"fheader\">Sanaluokka:</span>" +
	        " <span class=\"fsvalue\">%s</span>") % results.getresult()[0][0]

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return "Error: 1 parameter expected"
		return _word_class(db, paramlist[0])
	return "Error: unknown function"
