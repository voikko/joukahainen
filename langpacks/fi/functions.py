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

# This file contains language specific program code for Finnish

import hfaffix
import hfutils
import _config


WCHARS = u"abcdefghijklmnopqrstuvwxyzåäöszèéšžABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖŠŽÈÉŠŽ-'|"
# Checks if string looks like a valid word. This is a mandatory function.
def checkword(string):
	for c in string:
		if not c in WCHARS: return False
	return True



CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']
CHARACTERISTIC_VERB_FORMS = ['infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
                             'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
                             'imperfekti_pass']
# Inflection table for a Finnish noun or verb.
def word_inflection(db, wid, word, classid):
	if classid in [1, 2]:
		classdatafile = _config.HF_DATA + "/subst.aff"
		characteristic_forms = CHARACTERISTIC_NOUN_FORMS
	elif classid == 3:
		classdatafile = _config.HF_DATA + "/verb.aff"
		characteristic_forms = CHARACTERISTIC_VERB_FORMS
	else: return u"(taivutuksia ei ole saatavissa tämän sanaluokan sanoille)"
	
	results = db.query(("SELECT value FROM string_attribute_value " +
	                    "WHERE wid = %i AND aid = 1") % wid)
	if results.ntuples() != 1: return "(taivutuksia ei ole saatavilla, tarkista taivutusluokka)"
	result = results.getresult()[0]
	
	infclass_parts = unicode(result[0], 'UTF-8').split('-')
	if len(infclass_parts) == 1:
		infclass_main = unicode(result[0], 'UTF-8')
		grad_type = '-'
	elif len(infclass_parts) == 2:
		infclass_main = infclass_parts[0]
		grad_type = infclass_parts[1]
	else: return u"(virheellinen taivutusluokka)"
	
	word_classes = hfaffix.read_word_classes(classdatafile)
	tableid = u"inftable%i" % wid

	retdata = u''
	have_only_characteristic = True
	for word_class in word_classes:
		if not infclass_main in word_class['smcnames']: continue
		inflected_words = hfaffix.inflect_word(word, grad_type, word_class)
		if inflected_words == None: continue
		form = None
		inflist = []
		inflected_words.append((u'', u'', u''))
		for inflected_word in inflected_words:
			if form != inflected_word[0]:
				if form != None and len(inflist) > 0:
					if form in characteristic_forms:
						htmlclass = u' class="characteristic"'
					elif form[0] == u'!':
						htmlclass = u' class="characteristic"'
						form = form[1:]
					else:
						htmlclass = ''
						have_only_characteristic = False
					infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
					retdata = retdata + (u"<tr%s><td>%s</td><td>%s</td></tr>\n" %
					          (htmlclass, form, infs))
				inflist = []
				form = inflected_word[0]
			if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r' \
			   and not inflected_word[1] in inflist:
				inflist.append(inflected_word[1])
	
	table_header = u'<table class="inflection" id="%s">\n<tr><th colspan="2">' % tableid
	if not have_only_characteristic:
		table_header = table_header \
		               + u'<a href="javascript:switchDetailedDisplay(\'%s\');" id="%s"></a>' \
			     % (tableid, tableid + u'a')
	table_header = table_header + u'Taivutus</th></tr>\n'
	return table_header + retdata + u'</table>\n'

# Lists the language specific output types. This is a mandatory function
def jooutput_list_supported_types():
	types = []
	types.append(('malaga', u'Tulosta Suomi-malagan käyttämässä muodossa'))
	return types

# Language specific list output. This is a mandatory functions
def jooutput_call(req, outputtype, db, query):
	if outputtype == 'malaga':
		_jooutput_malaga(req, db, query)
	else:
		joheaders.error_page(req, _(u'Unsupported output type'))
