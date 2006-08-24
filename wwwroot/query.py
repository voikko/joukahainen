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

# This file contains methods to query the word database

from mod_python import apache

import sys
import _apply_config
import joheaders
import jotools
import jooutput
import jodb

_ = _apply_config.translation.ugettext

def form(req):
	db = jodb.connect()
	joheaders.page_header(req, _(u'Search database'))
	jotools.write(req, u'<form method="get" action="wlist">\n<p>')
	jotools.write(req, u'<label>%s: <input type="text" name="word" /></label>\n' % _(u'Word'))
	jotools.write(req, u'<label>%s <input type="checkbox" name="wordre" /></label></p><p>\n' \
	              % _(u'Use regular expression'))
	textattrs = db.query("SELECT aid, descr FROM attribute WHERE type = 1").getresult()
	jotools.write(req, u'<select name="textaid">\n')
	jotools.write(req, u'<option selected="1" value="">(%s)</option>\n' % _(u'select attribute'))
	for (aid, dsc) in textattrs:
		jotools.write(req, u'<option value="%i">%s</option>\n' % (aid, unicode(dsc, 'UTF-8')))
	jotools.write(req, u'</select> %s <input type="text" name="textvalue" /><br />\n' % _(u'is'))
	for (tname, tdesc) in jooutput.list_supported_types():
		if tname == 'html': selected = u'checked="checked"'
		else: selected = u''
		jotools.write(req, (u'<label><input type="radio" name="listtype" value="%s" %s>' +
		                    u'%s</label><br />\n') % (tname, selected, tdesc))
	jotools.write(req, u'</p><p><input type="submit" value="%s" /><input type="reset" value="%s" /></p>\n' \
	              % (_(u'Search'), _(u'Reset')))
	jotools.write(req, u'</form>\n')
	joheaders.page_footer(req)
	return "</html>"

def wlist(req):
	qselect = "SELECT w.wid, w.word, c.name AS classname, w.class FROM word w, wordclass c"
	conditions = ["w.class = c.classid"]
	word = jotools.get_param(req, 'word', u'')
	if word != u'':
		if not jotools.checkre(word):
			joheaders.error_page(req, _(u'Word has forbidden characters in it'))
			return "\n"
		if jotools.get_param(req, 'wordre', u'') == u'on': compop = 'SIMILAR TO'
		else: compop = '='
		conditions.append("w.word %s '%s'" % (compop, jotools.escape_sql_string(word)))
	aid = jotools.toint(jotools.get_param(req, 'textaid', u''))
	if aid != 0:
		value = jotools.get_param(req, 'textvalue', u'')
		if value == u'':
			cond = "w.wid NOT IN (SELECT wid FROM string_attribute_value WHERE aid = %i)" % aid
		else:
			cond = ("w.wid IN (SELECT wid FROM string_attribute_value " +
			        "WHERE aid = %i AND value = '%s')") % (aid, jotools.escape_sql_string(value))
		conditions.append(cond)
	# FIXME: user should be able to select the order
	order = "ORDER BY w.word, c.name, w.wid"
	# Build the full select clause
	if len(conditions) == 0:
		select = qselect + " " + order
	elif len(conditions) == 1:
		select = qselect + " WHERE " + conditions[0] + " " + order
	else:
		select = qselect + " WHERE " + conditions[0]
		for condition in conditions[1:]:
			select = select + " AND " + condition
		select = select + " " + order
	
	outputtype = jotools.get_param(req, "listtype", u'html')
	jooutput.call(req, outputtype, select)
	return "\n"
