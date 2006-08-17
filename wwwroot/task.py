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
import random

_ = _apply_config.translation.ugettext

def list(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	db = jodb.connect()
	tasks = db.query("SELECT t.tid, t.descr, t.sql, COUNT(DISTINCT tw.wid) FROM task t " +
	                 "LEFT JOIN task_word tw ON (t.tid = tw.tid) " +
		       "GROUP BY t.tid, t.descr, t.sql ORDER BY t.tid")
	if tasks.ntuples() == 0:
		joheaders.error_page(req, _(u'There are no tasks.'))
		return '\n'
	joheaders.list_page_header(req, u"Joukahainen &gt; %s" % _(u"tasks"), uid, uname)
	jotools.write(req, u"<p>%s:</p>\n" % _(u'Choose a task'))
	jotools.write(req, (u'<table class="border"><tr><th>%s</th><th>%s</th>' +
	                   u'<th>%s *</th><th>%s *</th></tr>\n') \
		         % (_(u'Task'), _(u'Total words'), _(u'Words left'), _(u'Completed')))
	for task in tasks.getresult():
		wordcount = db.query("SELECT COUNT(*) FROM (%s) AS q" % task[2]).getresult()[0][0]
		jotools.write(req, u'<tr><td><a href="work?tid=%i">' % task[0])
		jotools.write(req, u'%s</a></td>' % jotools.escape_html(unicode(task[1],'UTF-8')))
		jotools.write(req, u'<td>%i</td>' % wordcount)
		jotools.write(req, u'<td>%i</td>' % (wordcount - task[3]))
		if wordcount == 0: pleft = u'-'
		else: pleft = task[3] * 100 / wordcount
		jotools.write(req, u'<td>%s %%</td></tr>\n' % pleft)
	jotools.write(req, u"</table>\n")
	# "Words left" is an approximation, because all of the checked words may not belong to
	# this task any more. Calculating the exact numbers is too slow to do here.
	jotools.write(req, u"<p>*) %s.</p>" % _(u'Number of words left is an estimate'))
	joheaders.list_page_footer(req)
	return '</html>\n'

def show(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	tid = jotools.toint(jotools.get_param(req, "tid", "0"))
	if tid == 0:
		joheaders.error_page(req, _(u'Parameter %s is required') % u'tid')
		return '\n'
	words_per_page = 20
	db = jodb.connect()
	taskq = db.query("SELECT sql, orderby FROM task WHERE tid = %i" % tid)
	if taskq.ntuples() != 1:
		joheaders.error_page(req, u'Parameter %s is wrong' % u'tid')
		return '\n'
	tasksql = taskq.getresult()[0][0]
	taskorder = taskq.getresult()[0][1]
	results = db.query(("SELECT w.wid, w.word FROM word w, (%s) t " +
	                    "WHERE t.wid = w.wid AND w.wid NOT IN " +
		          "(SELECT tw.wid FROM task_word tw WHERE tw.tid = %i)" +
			"ORDER BY %s") % (tasksql, tid, taskorder))
	joheaders.page_header(req, u"Joukahainen &gt; %s %i" % (_(u'task'), tid))
	jotools.write(req, u'<div class="main">\n')
	jotools.write(req, u'<form method="post" action="save">\n')
	jotools.write(req, u'<table class="border">\n<tr><th>%s</th><th>%s</th></tr>\n' \
	                   % (_(u'OK'), _(u'Word')))
	firstword = random.randint(0, max(results.ntuples() - words_per_page, 0))
	restuples = results.getresult()
	for i in range(firstword, min(firstword + words_per_page, results.ntuples() - 1)):
		word = restuples[i]
		jotools.write(req, u'<tr><td><input type="checkbox" name="checked%i" /></td>' \
		                   % word[0])
		jotools.write(req, (u'<td><a href="../word/edit?wid=%i" target="right">%s' +
		                    u'</a></td></tr>\n') \
				% (word[0], jotools.escape_html(unicode(word[1], 'UTF-8'))))
	jotools.write(req, u'</table>')
	jotools.write(req, u'<p><input type="hidden" name="tid" value="%i" />' % tid)
	jotools.write(req, u'<input type="submit" value="%s"></form></p>' % _(u'Save checked'))
	jotools.write(req, u'</div>')
	joheaders.page_footer(req)
	return '</html>\n'

def work(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	tid = jotools.toint(jotools.get_param(req, "tid", "0"))
	if tid == 0:
		joheaders.error_page(req, _(u'Parameter %s is required') % u'tid')
		return '\n'
	joheaders.frame_header(req, u"Joukahainen &gt; %s %i" % (_(u'task'), tid))
	jotools.write(req, u'<frameset cols="20%, 80%">\n')
	jotools.write(req, u'<frame name="left" src="show?tid=%i" />\n' % tid)
	jotools.write(req, u'<frame name="right" />\n')
	jotools.write(req, u'</frameset>\n')
	joheaders.frame_footer(req)
	return '\n'

def save(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only POST requests are allowed'))
		return '\n'
	tid = jotools.toint(jotools.get_param(req, "tid", "0"))
	if tid == 0:
		joheaders.error_page(req, _(u'Parameter %s is required') % u'tid')
		return '\n'
	db = jodb.connect()
	for field in req.form.list:
		if field.name.startswith('checked'):
			wid = jotools.toint(field.name[7:])
			if wid == 0: continue
			db.query("INSERT INTO task_word(tid, wid, uid) VALUES(%i, %i, %i)" %
			         (tid, wid, uid))
	joheaders.redirect_header(req, u"show?tid=%i" % tid)
