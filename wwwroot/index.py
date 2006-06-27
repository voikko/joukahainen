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

# This file contains the index pages

from mod_python import apache

import _apply_config
import joheaders
import jotools
import jodb

def index(req):
	joheaders.page_header(req)
	db = jodb.connect()
	(uid, uname) = jotools.get_login_user(req, db)
	static_vars = {'UID': uid, 'UNAME': uname}
	jotools.process_template(req, db, static_vars, 'index_index', 'fi', 'joindex')
	joheaders.page_footer(req)
	return "</html>"
