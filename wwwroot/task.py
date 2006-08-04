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

# This file contains vocabulary wide edit/review task management

from mod_python import apache

import _config
import _apply_config
import joheaders
import jotools
import jodb

def list(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	db = jodb.connect()
	tasks = db.query("SELECT t.tid, t.descr, t.sql, COUNT(DISTINCT tw.tid) FROM task t " +
	                 "LEFT JOIN task_word tw ON (t.tid = tw.tid) " +
		       "GROUP BY t.tid, t.descr, t.sql ORDER BY t.tid")
	if tasks.ntuples() == 0:
		joheaders.error_page(req, u'Tehtäviä ei ole.')
		return '\n'
	joheaders.list_page_header(req, u"Joukahainen &gt; Tehtävät", uid, uname)
	jotools.write(req, u"<p>Valitse tehtävä:</p>\n")
	jotools.write(req, u'<table class="border"><tr><th>Tehtävä</th><th>Sanoja yhteensä</th>' +
	                   u'<th>Sanoja jäljellä</th><th>Tehtävästä suoritettu</th></tr>\n')
	for task in tasks.getresult():
		wordcount = db.query("SELECT COUNT(*) FROM (%s) AS q" % task[2]).getresult()[0][0]
		jotools.write(req, u'<tr><td><a href="work?tid=%i">' % task[0])
		jotools.write(req, u'%s</a></td>' % jotools.escape_html(unicode(task[1],'UTF-8')))
		jotools.write(req, u'<td>%i</td>' % wordcount)
		jotools.write(req, u'<td>%i</td>' % (wordcount - task[3]))
		jotools.write(req, u'<td>%i %%</td></tr>\n' % (task[3] * 100 / wordcount))
	jotools.write(req, u"</table>\n")
	joheaders.list_page_footer(req)
	return '</html>\n'

