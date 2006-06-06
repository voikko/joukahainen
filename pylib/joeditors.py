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

import hfaffix
import hfutils
import _config

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return "Error: word class %i does not exist" % classid
	return ("<span class=\"fheader\">Sanaluokka:</span>" +
	        " <span class=\"fsvalue\">%s</span>") % results.getresult()[0][0]

def _noun_inflection(db, wid, word):
	results = db.query(("SELECT value FROM string_attribute_value " +
	                    "WHERE wid = %i AND aid = 1") % wid)
	if results.ntuples() != 1:
		return "(no inflection data)"
	result = results.getresult()[0]
	
	infclass_parts = result[0].split('-')
	if len(infclass_parts) == 2:
		infclass_main = result[0]
		grad_type = '-'
	elif len(infclass_parts) == 3:
		infclass_main = infclass_parts[0]+'-'+infclass_parts[1]
		grad_type = infclass_parts[2]
	
	noun_classes = hfaffix.read_noun_classes(_config.HF_DATA + "/subst.aff")
	retdata = u"<table>\n<tr><th>Sijamuoto</th><th>Sana</th></tr>\n"
	for noun_class in noun_classes:
		if noun_class['cname'] != infclass_main: continue
		inflected_words = hfaffix.inflect_noun(word, grad_type, noun_class)
		if inflected_words == None: continue
		for inflected_word in inflected_words:
			if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r':
				retdata = retdata + ("<tr><td>%s</td><td>%s</td></tr>\n" %
				          (inflected_word[0], inflected_word[1]))
	return retdata + "</table>\n"

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return "Error: 1 parameter expected"
		return _word_class(db, paramlist[0])
	if funcname == 'noun_inflection':
		if len(paramlist) != 2: return "Error: 2 parameters expected"
		return _noun_inflection(db, paramlist[0], paramlist[1])
	return "Error: unknown function"
