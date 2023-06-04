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
	joheaders.page_header_navbar_level1(req, _('Search database'), uid, uname)
	jotools.write(req, '<form method="get" action="wlist">\n<p>')
	jotools.write(req, '<label>%s: <input type="text" name="word" /></label></p>\n' % _('Word'))
	jotools.write(req, '<p><label><input type="checkbox" name="wordre" /> %s</label>\n' \
	              % _('Use regular expression'))
	jotools.write(req, ' <b>%s</b> <label><input type="checkbox" name="wordsimplere" /> %s</label><br />\n' \
	              % (_('or'), _('Case insensitive search')))
	jotools.write(req, '<label><input type="checkbox" name="altforms" /> %s</label></p>\n' \
	              % _('Search from alternative spellings'))
	
	wclasses = db.query("SELECT classid, name FROM wordclass ORDER BY classid").getresult()
	jotools.write(req, '<h2>%s</h2>\n' % _('Word class'))
	jotools.write(req, '<p>%s ' % _('Word class is'))
	jotools.write(req, '<select name="wordclass">\n')
	jotools.write(req, '<option selected="selected" value="">(%s)</option>\n' % _('any'))
	for (classid, name) in wclasses:
		jotools.write(req, '<option value="%i">%s</option>\n' % (classid, str(name, 'UTF-8')))
	jotools.write(req, '</select></p>\n')
	
	textattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 1 ORDER BY descr, aid").getresult()
	jotools.write(req, '<h2>%s</h2>\n' % _('Text attributes'))
	jotools.write(req, '<p><select name="textaid">\n')
	jotools.write(req, '<option selected="selected" value="">(%s)</option>\n' % _('select attribute'))
	for (aid, dsc) in textattrs:
		jotools.write(req, '<option value="%i">%s</option>\n' % (aid, str(dsc, 'UTF-8')))
	jotools.write(req, '</select> %s <input type="text" name="textvalue" /><br />\n' % _('is'))
	
	flagattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 2 ORDER BY descr, aid").getresult()
	jotools.write(req, '</p><h2>%s</h2>' % _('Flags set'))
	jotools.write(req, '<ul class="cblist">')
	for (aid, dsc) in flagattrs:
		jotools.write(req, '<li><label><input type="checkbox" name="flagon%i" />%s</label></li>\n' \
		              % (aid, str(dsc, 'UTF-8')))
	jotools.write(req, '</ul>\n')
	jotools.write(req, '<h2>%s</h2>' % _('Flags not set'))
	jotools.write(req, '<ul class="cblist">')
	for (aid, dsc) in flagattrs:
		jotools.write(req, '<li><label><input type="checkbox" name="flagoff%i" />%s</label></li>\n' \
		              % (aid, str(dsc, 'UTF-8')))
	jotools.write(req, '</ul>\n')
	
	jotools.write(req, '<h2>%s</h2>\n<p>' % _('Output type'))
	for (tname, tdesc) in jooutput.list_supported_types():
		if tname == 'html': selected = 'checked="checked"'
		else: selected = ''
		jotools.write(req, ('<label><input type="radio" name="listtype" value="%s" %s />' +
		                    '%s</label><br />\n') % (tname, selected, tdesc))
	jotools.write(req, '</p><p><input type="submit" value="%s" /><input type="reset" value="%s" /></p>\n' \
	              % (_('Search'), _('Reset')))
	jotools.write(req, '</form>\n')
	joheaders.page_footer_plain(req)
	return '\n'

def listchanges(req, sdate = None, edate = None):
	db = jodb.connect()
	(uid, uname, editable) = jotools.get_login_user(req)
	joheaders.page_header_navbar_level1(req, _('List changes'), uid, uname)
	
	edt = datetime.datetime.now()
	sdt = edt - datetime.timedelta(days=1)
	if sdate != None:
		try:
			stime = time.strptime(sdate, '%Y-%m-%d')
			sdt = datetime.datetime(*stime[0:5])
		except:
			jotools.write(req, "<p>%s</p>\n" % _("Invalid start date"))
	if edate != None:
		try:
			etime = time.strptime(edate, '%Y-%m-%d')
			edt = datetime.datetime(*etime[0:5])
		except:
			jotools.write(req, "<p>%s</p>\n" % _("Invalid end date"))
	sdate_s = sdt.strftime('%Y-%m-%d')
	edate_s = edt.strftime('%Y-%m-%d')
	
	jotools.write(req, """
<form method="get" action="listchanges">
<label>%s <input type="text" name="sdate" value="%s"/></label><br />
<label>%s <input type="text" name="edate" value="%s"/></label><br />
<input type="submit" /> <input type="reset" />
</form>
	""" % (_('Start date'), sdate_s, _('End date'), edate_s))
	
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
	ORDER BY 2 DESC""" % (_('Word created').encode('UTF-8'), sdate_s, edate_s, sdate_s, edate_s));
	
	if results.ntuples() > 1000:
		jotools.write(req, '<p>%s</p>' % _('Too many changes, use narrower date interval.'))
		joheaders.page_footer_plain(req)
		return '\n'
	retstr = ''
	for result in results.getresult():
		wordlink = '<a href="../word/edit?wid=%i">%s</a>' \
		           % (result[6], jotools.escape_html(str(result[7], 'UTF-8')))
		date = result[1]
		user = jotools.escape_html(str(result[2], 'UTF-8')) + " " + \
		       jotools.escape_html(str(result[3], 'UTF-8')) + " (" + \
		       jotools.escape_html(str(result[0], 'UTF-8')) + ")"
		retstr = retstr + ('<div class="logitem"><p class="date">%s %s %s</p>\n' \
		                   % (wordlink, user, date))
		if result[4] != None:
			msg = jotools.escape_html(str(result[4], 'UTF-8')).strip()
			msg = msg.replace('\n', '<br />\n')
			retstr = retstr + '<p class="logmsg">%s</p>\n' % msg
		if result[5] != None:
			comment = jotools.escape_html(str(result[5], 'UTF-8')).strip()
			comment = comment.replace('\n', '<br />\n')
			comment = jotools.comment_links(comment)
			retstr = retstr + '<p class="comment">%s</p>\n' % comment
		retstr = retstr + "</div>\n"
	
	jotools.write(req, retstr)
	joheaders.page_footer_plain(req)
	return '\n'
