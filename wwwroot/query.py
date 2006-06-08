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

def listwords(req):
	joheaders.page_header(req)
	jotools.write(req, u"<h1>Kaikki sanat</h1>\n")
	db = jodb.connect()
	results = db.query("select wid, word from word")
	jotools.write(req, "<table><tr><th>Sana</th></tr>\n")
	for result in results.getresult():
		jotools.write(req, "<tr><td><a href=\"../word/edit?wid=%i\">%s</a></td></tr>\n" %
		              (result[0], unicode(result[1].decode('UTF-8'))))
	jotools.write(req, "</table>\n")
	joheaders.page_footer(req)
	return "</html>"
