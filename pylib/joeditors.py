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
import joindex
import jotools
import _config

def _word_class(db, classid):
	results = db.query("SELECT name FROM wordclass WHERE classid = %i" % classid)
	if results.ntuples() == 0:
		return u"Error: word class %i does not exist" % classid
	return (u"<span class=\"fheader\">Sanaluokka:</span>" +
	        u" <span class=\"fsvalue\">%s</span>") % unicode(results.getresult()[0][0], 'UTF-8')

CHARACTERISTIC_NOUN_FORMS = ['nominatiivi', 'genetiivi', 'partitiivi', 'illatiivi',
                             'genetiivi_mon', 'partitiivi_mon', 'illatiivi_mon']

def _noun_inflection(db, wid, word):
	results = db.query(("SELECT value FROM string_attribute_value " +
	                    "WHERE wid = %i AND aid = 1") % wid)
	if results.ntuples() != 1: return "(taivutuksia ei ole saatavilla)"
	result = results.getresult()[0]
	
	infclass_parts = unicode(result[0], 'UTF-8').split('-')
	if len(infclass_parts) == 1:
		infclass_main = unicode(result[0], 'UTF-8')
		grad_type = '-'
	elif len(infclass_parts) == 2:
		infclass_main = infclass_parts[0]
		grad_type = infclass_parts[1]
	else: return u"(virheellinen taivutusluokka)"
	
	noun_classes = hfaffix.read_noun_classes(_config.HF_DATA + "/subst.aff")
	tableid = u"inftable%i" % wid

	retdata = (u'<table class="inflection" id="%s">\n<tr><th colspan="2">' +
	           u'<a onclick="switchDetailedDisplay(\'%s\');" id="%s"></a> Taivutus</th></tr>\n') \
		% (tableid, tableid, tableid + u'a')
	for noun_class in noun_classes:
		if not infclass_main in noun_class['smcnames']: continue
		inflected_words = hfaffix.inflect_noun(word, grad_type, noun_class)
		if inflected_words == None: continue
		form = None
		inflist = []
		inflected_words.append((u'', u'', u''))
		for inflected_word in inflected_words:
			if form != inflected_word[0]:
				if form != None and len(inflist) > 0:
					if form in CHARACTERISTIC_NOUN_FORMS:
						htmlclass = u' class="characteristic"'
					else:
						htmlclass = ''
					infs = reduce(lambda x, y: u"%s, %s" % (x, y), inflist)
					retdata = retdata + (u"<tr%s><td>%s</td><td>%s</td></tr>\n" %
					          (htmlclass, form, infs))
				inflist = []
				form = inflected_word[0]
			if hfutils.read_option(inflected_word[2], 'ps', '-') != 'r' \
			   and not inflected_word[1] in inflist:
				inflist.append(inflected_word[1])
	return retdata + u"</table>\n"

def _flag_attributes(db, wid):
	results = db.query(("SELECT a.descr FROM attribute a, flag_attribute_value f " +
	                    "WHERE a.aid = f.aid AND a.type = 2 AND f.wid = %i") % wid)
	if results.ntuples() == 0: return u"(ei asetettuja lippuja)"
	retdata = u"<ul>\n"
	for result in results.getresult():
		retdata = retdata + (u"<li>%s</li>\n" % unicode(result[0], 'UTF-8'))
	return retdata + u"</ul>\n"

def _string_attribute(db, wid, aid, editable):
	results = db.query(("SELECT s.value FROM string_attribute_value s " +
	                    "WHERE s.wid = %i AND s.aid = %i") % (wid, aid))
	if editable:
		if results.ntuples() == 0: oldval = u'""'
		else: oldval = jotools.escape_form_value(unicode(results.getresult()[0][0], 'UTF-8'))
		return u'<input type="text" value=%s name="string%i">' % (oldval, aid)
	else:
		if results.ntuples() == 0 : return u"(ei asetettu)"
		return unicode(results.getresult()[0][0], 'UTF-8')

def _related_words(db, wid):
	results = db.query("SELECT related_word FROM related_word WHERE wid = %i" % wid)
	if results.ntuples() == 0: return u"(ei asetettu)"
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % unicode(result[0], 'UTF-8'))
	return retdata + "</ul>\n"

def _main_form_start(db, editable):
	if editable:
		return u'<form method="POST" action="change" class="subform">'
	else:
		return u''

def _main_form_end(db, wid, editable):
	if editable:
		return u'''<p><input type="submit" value="Tallenna muutokset">
<input type="reset" value="Peruuta muutokset">
<input type="hidden" name="wid" value="%i"></p>
</form>''' % wid
	else:
		return u''

def _message_log(db, wid):
	results = db.query(("SELECT u.uname, e.etime, e.message FROM appuser u, event e " +
	                    "WHERE u.uid = e.euser AND e.eword = %i ORDER BY e.etime") % wid)
	retstr = u""
	for result in results.getresult():
		retstr = retstr + (u"<p>%s %s: %s</p>\n" % (result[1], result[0],
		         jotools.escape_html(unicode(result[2], 'UTF-8'))))
	return retstr

def _flag_edit_form(db, wid, classid):
	results = db.query(("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
	                    "FROM attribute_class ac, attribute a " +
	                    "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = %i) " +
	                    "WHERE a.aid = ac.aid AND ac.classid = %i AND a.type = 2" +
			"ORDER BY a.descr") % (wid, classid))
	if results.ntuples() == 0: return u"(ei asetettavissa olevia lippuja)"
	retstr = u'<form method="POST" action="flags">\n'
	for result in results.getresult():
		retstr = retstr + u'<input type="checkbox" value="on" name="attr%i"' % result[0]
		if result[2] == 't': retstr = retstr + u' checked="true"'
		retstr = retstr + u'>' + jotools.escape_html(unicode(result[1], 'UTF-8')) + u'<br />\n'
	retstr = retstr + u'<input type="hidden" name="wid" value="%i">\n' % wid + \
	                  u'<input type="submit" value="Tallenna muutokset">\n' + \
	                  u'<input type="reset" value="Peruuta muutokset">\n' + \
	                  u'</form>'
	return retstr

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
		if len(paramlist) != 3: return u"Error: 3 parameters expected"
		return _string_attribute(db, paramlist[0], paramlist[1], paramlist[2])
	if funcname == 'related_words':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _related_words(db, paramlist[0])
	if funcname == 'login_logout':
		if len(paramlist) != 2: return u"Error: 2 parameters expected"
		return joindex.login_logout(db, paramlist[0], paramlist[1])
	if funcname == 'main_form_start':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _main_form_start(db, paramlist[0])
	if funcname == 'main_form_end':
		if len(paramlist) != 2: return u"Error: 2 parameters expected"
		return _main_form_end(db, paramlist[0], paramlist[1])
	if funcname == 'message_log':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _message_log(db, paramlist[0])
	if funcname == 'flag_edit_form':
		if len(paramlist) != 2: return u"Error: 2 parameters expected"
		return _flag_edit_form(db, paramlist[0], paramlist[1])
	return u"Error: unknown function"
