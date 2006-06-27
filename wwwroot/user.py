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

# This file contains user administration functions

from mod_python import apache

import sys
import _config
import _apply_config
import joheaders
import jotools
import jodb
import sha
import time
import os
import random

def login(req, username = None, password = None):
	if req.method != 'POST':
		joheaders.page_header(req)
		jotools.write(req, u"Vain POST-pyynnöt ovat sallittuja")
		joheaders.page_footer(req)
		return "</html>"
	
	if username == None or password == None or not jotools.checkuname(unicode(username, 'UTF-8')):
		joheaders.page_header(req)
		jotools.write(req, u"Käyttäjätunnus tai salasana puuttuu tai käyttäjätunnus on väärin")
		joheaders.page_footer(req)
		return "</html>"
	
	pwhash = sha.new(_config.PW_SALT + unicode(password, 'UTF-8')).hexdigest()
	db = jodb.connect()
	results = db.query(("select uid from appuser where uname = '%s' and pwhash = '%s' " +
	                    "and disabled = FALSE") % (username, pwhash))
	if results.ntuples() == 0:
		joheaders.page_header(req)
		jotools.write(req, u"Käyttäjätunnus tai salasana on väärin")
		joheaders.page_footer(req)
		return "</html>"
	
	uid = results.getresult()[0][0]
	
	# Generate session key
	sesssha = sha.new()
	sesssha.update(username)
	sesssha.update(pwhash)
	if hasattr(os, 'urandom'): # this is only available in Python >= 2.4
		sesssha.update(os.urandom(15))
	else:
		sesssha.update(time.time())
		sesssha.update(random.random())
		sesssha.update(os.times())
	sesskey = sesssha.hexdigest()
	
	db.query(("update appuser set session_key = '%s', session_exp = CURRENT_TIMESTAMP + " +
	          "interval '%i seconds' where uid = %i") % (sesskey, _config.SESSION_TIMEOUT, uid))
	req.headers_out['Set-Cookie'] = 'session=%s; path=%s' % (sesskey, _config.WWW_ROOT_DIR)
	joheaders.redirect_header(req, u"..")
	return "</html>"

def logout(req):
	if req.method != 'POST':
		joheaders.page_header(req)
		jotools.write(req, u"Vain POST-pyynnöt ovat sallittuja")
		joheaders.page_footer(req)
		return "</html>"
	session = jotools.get_session(req)
	if session != '':
		db = jodb.connect()
		db.query(("update appuser set session_key = NULL, session_exp = NULL " +
		          "where session_key = '%s'") % session)
	req.headers_out['Set-Cookie'] = 'session=; path=%s; expires=Thu, 01-Jan-1970 00:00:01 GMT' \
	                                % _config.WWW_ROOT_DIR
	joheaders.redirect_header(req, u"..")
	return "</html>"
