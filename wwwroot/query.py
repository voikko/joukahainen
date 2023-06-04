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
