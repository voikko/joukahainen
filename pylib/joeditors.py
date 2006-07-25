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
CHARACTERISTIC_VERB_FORMS = ['infinitiivi_1', 'preesens_yks_1', 'imperfekti_yks_3',
                             'kondit_yks_3', 'imperatiivi_yks_3', 'partisiippi_2',
                             'imperfekti_pass']

def _word_inflection(db, wid, word, classid):
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

	retdata = (u'<table class="inflection" id="%s">\n<tr><th colspan="2">' +
	           u'<a href="javascript:switchDetailedDisplay(\'%s\');" id="%s"></a> Taivutus</th></tr>\n') \
		% (tableid, tableid, tableid + u'a')
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
	if results.ntuples() == 0: return u"<p>(ei asetettuja lippuja)</p>"
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
		return u'<input type="text" value=%s size="60" name="string%i" />' % (oldval, aid)
	else:
		if results.ntuples() == 0 : return u"(ei asetettu)"
		return unicode(results.getresult()[0][0], 'UTF-8')

def _related_words(db, wid):
	results = db.query("SELECT related_word FROM related_word WHERE wid = %i" % wid)
	if results.ntuples() == 0: return u"<p>(ei asetettu)</p>"
	retdata = "<ul>\n"
	for result in results.getresult():
		retdata = retdata + ("<li>%s</li>\n" % unicode(result[0], 'UTF-8'))
	return retdata + "</ul>\n"

def _main_form_start(db, editable):
	if editable:
		return u'<form method="post" action="change" class="subform">'
	else:
		return u''

def _main_form_end(db, wid, editable):
	if editable:
		return u'''<p><span class="fheader">Lisää kommentti:</span>
<textarea name="comment" cols="80" rows="5"></textarea></p>
<p><input type="submit" value="Tallenna muutokset" />
<input type="reset" value="Peruuta muutokset" />
<input type="hidden" name="wid" value="%i" /></p>
</form>''' % wid
	else:
		return u''

def _message_log(db, wid):
	results = db.query(("SELECT u.uname, to_char(e.etime, 'YYYY-MM-DD HH24:MI:SS'), e.message, " +
	                    "e.comment, coalesce(u.firstname, ''), coalesce(u.lastname, '') " +
	                    "FROM appuser u, event e " +
	                    "WHERE u.uid = e.euser AND e.eword = %i ORDER BY e.etime") % wid)
	if results.ntuples() == 0:
		return u'<p>(ei muutostietoja)</p>'
	retstr = u""
	for result in results.getresult():
		date = result[1]
		user = jotools.escape_html(unicode(result[4], 'UTF-8')) + u" " + \
		       jotools.escape_html(unicode(result[5], 'UTF-8')) + u" (" + \
		       jotools.escape_html(unicode(result[0], 'UTF-8')) + u")"
		retstr = retstr + (u'<div class="logitem"><p class="date">%s %s</p>\n' \
		                   % (user, date))
		if result[2] != None:
			msg = jotools.escape_html(unicode(result[2], 'UTF-8')).strip()
			msg = msg.replace(u'\n', u'<br />\n')
			retstr = retstr + u'<p class="logmsg">%s</p>\n' % msg
		if result[3] != None:
			comment = jotools.escape_html(unicode(result[3], 'UTF-8')).strip()
			comment = comment.replace(u'\n', u'<br />\n')
			retstr = retstr + u'<p class="comment">%s</p>\n' % comment
		retstr = retstr + u"</div>\n"
	return retstr

def _flag_edit_form(db, wid, classid):
	results = db.query(("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
	                    "FROM attribute_class ac, attribute a " +
	                    "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = %i) " +
	                    "WHERE a.aid = ac.aid AND ac.classid = %i AND a.type = 2" +
			"ORDER BY a.descr") % (wid, classid))
	if results.ntuples() == 0: return u"(ei asetettavissa olevia lippuja)"
	retstr = u'<form method="post" action="flags"><p>\n'
	for result in results.getresult():
		retstr = retstr + u'<label><input type="checkbox" value="on" name="attr%i"' % result[0]
		if result[2] == 't': retstr = retstr + u' checked="checked"'
		retstr = retstr + u' />' + jotools.escape_html(unicode(result[1], 'UTF-8'))
		retstr = retstr + u'</label><br />\n'
	retstr = retstr + u'<input type="hidden" name="wid" value="%i" /></p>\n' % wid + \
	                  u'<p><span class="fheader">Lisää kommentti:</span>\n' + \
	                  u'<textarea name="comment" cols="80" rows="5"></textarea></p>\n' + \
	                  u'<p><input type="submit" value="Tallenna muutokset" />\n' + \
	                  u'<input type="reset" value="Peruuta muutokset" />\n' + \
	                  u'</p></form>'
	return retstr

def _rwords_edit_form(db, wid):
	results = db.query(("SELECT r.rwid, r.related_word FROM related_word r " +
	                    "WHERE r.wid = %i ORDER BY r.related_word") % wid)
	retstr = u'<form method="post" action="rwords">\n'
	if results.ntuples() > 0:
		retstr = retstr + u'<h2>Poista kirjoitusasuja</h2>\n<p>\n'
	for result in results.getresult():
		retstr = retstr + u'<label><input type="checkbox" value="on" name="rword%i" />' % result[0]
		retstr = retstr + jotools.escape_html(unicode(result[1], 'UTF-8'))
		retstr = retstr + u'</label><br />\n'
	if results.ntuples() > 0:
		retstr = retstr + u'</p>\n'
	retstr = retstr + u'<p><span class="fheader">Lisää kirjoitusasuja</span>\n' + \
	                  u'<input type="text" size="80" name="add" /></p>\n' + \
	                  u'<p><span class="fheader">Lisää kommentti:</span>\n' + \
	                  u'<textarea name="comment" cols="80" rows="5"></textarea></p>\n' + \
	                  u'<p><input type="hidden" name="wid" value="%i" />\n' % wid + \
	                  u'<input type="submit" value="Tallenna muutokset" />\n' + \
	                  u'<input type="reset" value="Peruuta muutokset" /></p>\n' + \
	                  u'</form>'
	return retstr

def call(db, funcname, paramlist):
	if funcname == 'word_class':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _word_class(db, paramlist[0])
	if funcname == 'word_inflection':
		if len(paramlist) != 3: return u"Error: 3 parameters expected"
		return _word_inflection(db, paramlist[0], paramlist[1], paramlist[2])
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
		if len(paramlist) != 3: return u"Error: 3 parameters expected"
		return joindex.login_logout(db, paramlist[0], paramlist[1], paramlist[2])
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
	if funcname == 'rwords_edit_form':
		if len(paramlist) != 1: return u"Error: 1 parameter expected"
		return _rwords_edit_form(db, paramlist[0])
	return u"Error: unknown function"
