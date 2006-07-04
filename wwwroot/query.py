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
import jodb

def listwords(req, offset = None, limit = None):
	joheaders.page_header(req)
	jotools.write(req, u"<h1>Kaikki sanat</h1>\n")
	db = jodb.connect()
	
	if offset == None: offset_s = u'0'
	else: offset_s = `jotools.toint(offset)`
	
	if limit == None: limit_s = u'200'
	elif jotools.toint(limit) == 0: limit_s = u'ALL'
	else: limit_s = `jotools.toint(limit)`
	
	results = db.query("SELECT w.wid, w.word, c.name FROM word w, wordclass c " +
	                   "WHERE w.class = c.classid ORDER BY w.word, c.name, w.wid LIMIT %s OFFSET %s" \
		         % (limit_s, offset_s))
	if results.ntuples() == 0:
		jotools.write(req, u"<p>Hakuehdon mukaisia sanoja ei löydy</p>\n")
	else:
		jotools.write(req, u"<table><tr><th>Sana</th><th>Sanaluokka</th></tr>\n")
		for result in results.getresult():
			jotools.write(req, u"<tr><td><a href=\"../word/edit?wid=%i\">%s</a></td><td>%s</td></tr>\n" %
			              (result[0], unicode(result[1], 'UTF-8'), unicode(result[2], 'UTF-8')))
		jotools.write(req, u"</table>\n")
		if not limit_s == u'ALL' and results.ntuples() == jotools.toint(limit_s):
			jotools.write(req, (u'<p><a href="listwords?offset=%i&limit=%s">' +
			              u"Lisää tuloksia ...</a></p>\n") % (int(offset_s)+int(limit_s), limit_s))
	joheaders.page_footer(req)
	return "</html>"

def findword(req, word = None):
	if word == None: 
		joheaders.error_page(req, u"Parametri word on pakollinen")
		return "\n"
	if not jotools.checkword(unicode(word, 'UTF-8')):
		joheaders.error_page(req, u"Annetussa sanassa on kielletyjä merkkejä")
		return "\n"
	word_s = jotools.escape_sql_string(unicode(word, 'UTF-8'))
	
	db = jodb.connect()
	results = db.query(("SELECT w.wid, w.word, c.name FROM word w, wordclass c WHERE w.class = c.classid " +
	                   "AND w.word = '%s' ORDER BY w.word, c.name, w.wid") % word_s)
	if results.ntuples() == 0:
		joheaders.page_header(req)
		jotools.write(req, u"<p>Annettua sanaa ei löytynyt</p>\n")
	elif results.ntuples() == 1:
		joheaders.redirect_header(req, u"../word/edit?wid=%i" % results.getresult()[0][0])
		return "\n"
	else:
		joheaders.page_header(req)
		jotools.write(req, "<table><tr><th>Sana</th><th>Sanaluokka</th></tr>\n")
		for result in results.getresult():
			jotools.write(req, "<tr><td><a href=\"../word/edit?wid=%i\">%s</a></td><td>%s</td></tr>\n" %
			              (result[0], unicode(result[1], 'UTF-8'), unicode(result[2], 'UTF-8')))
		jotools.write(req, "</table>\n")
	joheaders.page_footer(req)
	return "</html>"
