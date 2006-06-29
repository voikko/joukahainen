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

# This file contains the word editor

from mod_python import apache

import sys
import _apply_config
import joheaders
import jotools
import jodb

def edit(req, wid = None):
	joheaders.page_header(req)
	if (wid == None): return "Parametri wid on pakollinen\n"
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		jotools.write(req, u"Sanaa %i ei ole\n" % wid_n)
	else:
		wordinfo = results.getresult()[0]
		(uid, uname, editable) = jotools.get_login_user(req, db)
		static_vars = {'WID': wid_n, 'WORD': unicode(wordinfo[0], 'UTF-8'), 'CLASSID': wordinfo[1],
		               'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
		jotools.process_template(req, db, static_vars, 'word_edit', 'fi', 'joeditors')
	joheaders.page_footer(req)
	return "</html>"
