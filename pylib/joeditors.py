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
import types
import _config

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return "Error: word class %i does not exist" % classid
	return ("<span class=\"fheader\">Sanaluokka:</span>" +
	        " <span class=\"fsvalue\">%s</span>") % results.getresult()[0][0]

CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']

def _noun_inflection(db, wid, word):
	results = db.query(("SELECT value FROM string_attribute_value " +
	                    "WHERE wid = %i AND aid = 1") % wid)
	if results.ntuples() != 1: return "(taivutuksia ei ole saatavilla)"
	result = results.getresult()[0]
	
	infclass_parts = result[0].split('-')
	if len(infclass_parts) == 1:
		infclass_main = result[0]
		grad_type = '-'
	elif len(infclass_parts) == 2:
		infclass_main = infclass_parts[0]
		grad_type = infclass_parts[1]
	else: return u"(virheellinen taivutusluokka)"
	
	noun_classes = hfaffix.read_noun_classes(_config.HF_DATA + "/subst.aff")
	retdata = u"<table class=\"inflection\">\n<tr><th colspan=\"2\">Taivutus</th></tr>\n"
	for noun_class in noun_classes:
		if not infclass_main in noun_class['smcnames']: continue
		inflected_words = hfaffix.inflect_noun(word, grad_type, noun_class)
		if inflected_words == None: continue
		for inflected_word in inflected_words:
			if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r':
				if inflected_word[0] in CHARACTERISTIC_NOUN_FORMS:
					htmlclass = u' class="characteristic"'
				else:
					htmlclass = ''
				retdata = retdata + (u"<tr%s><td>%s</td><td>%s</td></tr>\n" %
				          (htmlclass, inflected_word[0], inflected_word[1]))
	return retdata + u"</table>\n"

def _flag_attributes(db, wid):
	results = db.query(("SELECT a.descr FROM attribute a, flag_attribute_value f " +
	                    "WHERE a.aid = f.aid AND a.type = 2 AND f.wid = %i") % wid)
	if results.ntuples() == 0: return "(ei asetettuja lippuja)"
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % result[0])
	return retdata + "</ul>\n"

def _string_attribute(db, wid, aid):
	results = db.query(("SELECT s.value FROM string_attribute_value s " +
	                    "WHERE s.wid = %i AND s.aid = %i") % (wid, aid))
	if results.ntuples() == 0: return u"(ei asetettu)"
	return results.getresult()[0][0]

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _word_class(db, paramlist[0])
	if funcname == 'noun_inflection':
		if len(paramlist) != 2: return u"Error: 2 parameters expected"
		return _noun_inflection(db, paramlist[0], paramlist[1])
	if funcname == 'flag_attributes':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _flag_attributes(db, paramlist[0])
	if funcname == 'string_attribute':
		if len(paramlist) != 2: return u"Error: 2 parameters expected"
		return _string_attribute(db, paramlist[0], paramlist[1])
	return u"Error: unknown function"
