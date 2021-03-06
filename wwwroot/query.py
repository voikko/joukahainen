# -*- coding: utf-8 -*-

# Copyright 2006 - 2009 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains methods to query the word database

from mod_python import apache

import sys
import datetime
import time
import re
import _apply_config
import joheaders
import jotools
import jooutput
import jodb

_ = _apply_config.translation.ugettext

def form(req):
	db = jodb.connect()
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, _(u'Search database'), uid, uname)
	jotools.write(req, u'<form method="get" action="wlist">\n<p>')
	jotools.write(req, u'<label>%s: <input type="text" name="word" /></label></p>\n' % _(u'Word'))
	jotools.write(req, u'<p><label><input type="checkbox" name="wordre" /> %s</label>\n' \
	              % _(u'Use regular expression'))
	jotools.write(req, u' <b>%s</b> <label><input type="checkbox" name="wordsimplere" /> %s</label><br />\n' \
	              % (_(u'or'), _(u'Case insensitive search')))
	jotools.write(req, u'<label><input type="checkbox" name="altforms" /> %s</label></p>\n' \
	              % _(u'Search from alternative spellings'))
	
	wclasses = db.query("SELECT classid, name FROM wordclass ORDER BY classid").getresult()
	jotools.write(req, u'<h2>%s</h2>\n' % _(u'Word class'))
	jotools.write(req, u'<p>%s ' % _(u'Word class is'))
	jotools.write(req, u'<select name="wordclass">\n')
	jotools.write(req, u'<option selected="selected" value="">(%s)</option>\n' % _(u'any'))
	for (classid, name) in wclasses:
		jotools.write(req, u'<option value="%i">%s</option>\n' % (classid, unicode(name, 'UTF-8')))
	jotools.write(req, u'</select></p>\n')
	
	textattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 1 ORDER BY descr, aid").getresult()
	jotools.write(req, u'<h2>%s</h2>\n' % _(u'Text attributes'))
	jotools.write(req, u'<p><select name="textaid">\n')
	jotools.write(req, u'<option selected="selected" value="">(%s)</option>\n' % _(u'select attribute'))
	for (aid, dsc) in textattrs:
		jotools.write(req, u'<option value="%i">%s</option>\n' % (aid, unicode(dsc, 'UTF-8')))
	jotools.write(req, u'</select> %s <input type="text" name="textvalue" /><br />\n' % _(u'is'))
	
	flagattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 2 ORDER BY descr, aid").getresult()
	jotools.write(req, u'</p><h2>%s</h2>' % _(u'Flags set'))
	jotools.write(req, u'<ul class="cblist">')
	for (aid, dsc) in flagattrs:
		jotools.write(req, u'<li><label><input type="checkbox" name="flagon%i" />%s</label></li>\n' \
		              % (aid, unicode(dsc, 'UTF-8')))
	jotools.write(req, u'</ul>\n')
	jotools.write(req, u'<h2>%s</h2>' % _(u'Flags not set'))
	jotools.write(req, u'<ul class="cblist">')
	for (aid, dsc) in flagattrs:
		jotools.write(req, u'<li><label><input type="checkbox" name="flagoff%i" />%s</label></li>\n' \
		              % (aid, unicode(dsc, 'UTF-8')))
	jotools.write(req, u'</ul>\n')
	
	jotools.write(req, u'<h2>%s</h2>\n<p>' % _(u'Output type'))
	for (tname, tdesc) in jooutput.list_supported_types():
		if tname == 'html': selected = u'checked="checked"'
		else: selected = u''
		jotools.write(req, (u'<label><input type="radio" name="listtype" value="%s" %s />' +
		                    u'%s</label><br />\n') % (tname, selected, tdesc))
	jotools.write(req, u'</p><p><input type="submit" value="%s" /><input type="reset" value="%s" /></p>\n' \
	              % (_(u'Search'), _(u'Reset')))
	jotools.write(req, u'</form>\n')
	joheaders.page_footer_plain(req)
	return '\n'

def wlist(req):
	# The select clause
	qselect = "SELECT w.wid, w.word, c.name AS classname, w.class FROM word w, wordclass c"
	
	# Initial conditions
	conditions = ["w.class = c.classid"]
	
	# Word form conditions
	word = jotools.get_param(req, 'word', u'')
	if word != u'':
		if not jotools.checkre(word):
			joheaders.error_page(req, _(u'Word has forbidden characters in it'))
			return "\n"
		if jotools.get_param(req, 'wordre', u'') == u'on':
			try:
				re.compile(word)
			except re.error:
				joheaders.error_page(req, _(u'Search string is not a valid regular expression'))
				return "\n"
			compop = '~*'
			compword = jotools.expandre(word)
		elif jotools.get_param(req, 'wordsimplere', u'') == u'on':
			compop = 'ILIKE'
			compword = word
		else:
			compop = '='
			compword = word
		# Use subquery if searching from alternative forms
		cond = "w.word %s '%s'" % (compop, jotools.escape_sql_string(compword))
		if jotools.get_param(req, 'altforms', u'') == u'on':
			cond = cond + " OR w.wid IN (" + \
			       "SELECT rw.wid FROM related_word rw WHERE " + \
			       "replace(replace(rw.related_word, '=', ''), '|', '') %s '%s')" \
			       % (compop, jotools.escape_sql_string(compword))
		conditions.append(cond)
	
	# Word class conditions
	wclass = jotools.toint(jotools.get_param(req, 'wordclass', u''))
	if wclass > 0:
		conditions.append("w.class = %i" % wclass)
	
	# Text attribute conditions
	aid = jotools.toint(jotools.get_param(req, 'textaid', u''))
	if aid != 0:
		value = jotools.get_param(req, 'textvalue', u'')
		if value == u'':
			cond = "w.wid NOT IN (SELECT wid FROM string_attribute_value WHERE aid = %i)" % aid
		else:
			cond = ("w.wid IN (SELECT wid FROM string_attribute_value " +
			        "WHERE aid = %i AND value = '%s')") % (aid, jotools.escape_sql_string(value))
		conditions.append(cond)
	
	# Flag conditions
	for field in req.form.list:
		if field.name.startswith('flagon'):
			aid = jotools.toint(field.name[6:])
			if jotools.get_param(req, 'flagon%i' % aid, u'') == u'on':
				cond = "w.wid IN (SELECT wid FROM flag_attribute_value WHERE aid = %i)" % aid
				conditions.append(cond)
		if field.name.startswith('flagoff'):
			aid = jotools.toint(field.name[7:])
			if jotools.get_param(req, 'flagoff%i' % aid, u'') == u'on':
				cond = "w.wid NOT IN (SELECT wid FROM flag_attribute_value WHERE aid = %i)" % aid
				conditions.append(cond)
	
	# FIXME: user should be able to select the order
	order = "ORDER BY w.word, c.name, w.wid"
	
	# Build the full select clause
	if len(conditions) == 0:
		select = qselect + " " + order
	elif len(conditions) == 1:
		select = qselect + " WHERE (" + conditions[0] + ") " + order
	else:
		select = qselect + " WHERE (" + conditions[0]
		for condition in conditions[1:]:
			select = select + ") AND (" + condition
		select = select + ") " + order
	
	outputtype = jotools.get_param(req, "listtype", u'html')
	jooutput.call(req, outputtype, select)
	return "\n"

def listchanges(req, sdate = None, edate = None):
	db = jodb.connect()
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, _(u'List changes'), uid, uname)
	
	edt = datetime.datetime.now()
	sdt = edt - datetime.timedelta(days=1)
	if sdate != None:
		try:
			stime = time.strptime(sdate, u'%Y-%m-%d')
			sdt = datetime.datetime(*stime[0:5])
		except:
			jotools.write(req, "<p>%s</p>\n" % _("Invalid start date"))
	if edate != None:
		try:
			etime = time.strptime(edate, u'%Y-%m-%d')
			edt = datetime.datetime(*etime[0:5])
		except:
			jotools.write(req, "<p>%s</p>\n" % _("Invalid end date"))
	sdate_s = sdt.strftime('%Y-%m-%d')
	edate_s = edt.strftime('%Y-%m-%d')
	
	jotools.write(req, u"""
<form method="get" action="listchanges">
<label>%s <input type="text" name="sdate" value="%s"/></label><br />
<label>%s <input type="text" name="edate" value="%s"/></label><br />
<input type="submit" /> <input type="reset" />
</form>
	""" % (_(u'Start date'), sdate_s, _(u'End date'), edate_s))
	
	# Increase edt by one day to make the the SQL between operator act on timestamps
	# in a more intuitive way.
	edt = edt + datetime.timedelta(days=1)
	edate_s = edt.strftime('%Y-%m-%d')
	
	results = db.query("""
	SELECT u.uname, to_char(w.ctime, 'YYYY-MM-DD HH24:MI:SS'),
	       coalesce(u.firstname, ''), coalesce(u.lastname, ''),
	       '%s', NULL, w.wid, w.word
	FROM word w, appuser u WHERE w.cuser = u.uid AND w.ctime BETWEEN '%s' AND '%s'
	UNION
	SELECT u.uname, to_char(e.etime, 'YYYY-MM-DD HH24:MI:SS'),
	       coalesce(u.firstname, ''), coalesce(u.lastname, ''),
	       e.message, e.comment, w.wid, w.word
	FROM appuser u, event e, word w WHERE u.uid = e.euser AND e.eword = w.wid
	AND e.etime BETWEEN '%s' AND '%s'
	ORDER BY 2 DESC""" % (_(u'Word created').encode('UTF-8'), sdate_s, edate_s, sdate_s, edate_s));
	
	if results.ntuples() > 1000:
		jotools.write(req, u'<p>%s</p>' % _(u'Too many changes, use narrower date interval.'))
		joheaders.page_footer_plain(req)
		return '\n'
	retstr = u''
	for result in results.getresult():
		wordlink = u'<a href="../word/edit?wid=%i">%s</a>' \
		           % (result[6], jotools.escape_html(unicode(result[7], 'UTF-8')))
		date = result[1]
		user = jotools.escape_html(unicode(result[2], 'UTF-8')) + u" " + \
		       jotools.escape_html(unicode(result[3], 'UTF-8')) + u" (" + \
		       jotools.escape_html(unicode(result[0], 'UTF-8')) + u")"
		retstr = retstr + (u'<div class="logitem"><p class="date">%s %s %s</p>\n' \
		                   % (wordlink, user, date))
		if result[4] != None:
			msg = jotools.escape_html(unicode(result[4], 'UTF-8')).strip()
			msg = msg.replace(u'\n', u'<br />\n')
			retstr = retstr + u'<p class="logmsg">%s</p>\n' % msg
		if result[5] != None:
			comment = jotools.escape_html(unicode(result[5], 'UTF-8')).strip()
			comment = comment.replace(u'\n', u'<br />\n')
			comment = jotools.comment_links(comment)
			retstr = retstr + u'<p class="comment">%s</p>\n' % comment
		retstr = retstr + u"</div>\n"
	
	jotools.write(req, retstr)
	joheaders.page_footer_plain(req)
	return '\n'
