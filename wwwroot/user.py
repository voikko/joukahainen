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

def login(req, wid = None):
	if req.method != 'POST':
		joheaders.error_page(req, u"Vain POST-pyynnöt ovat sallittuja")
		return '\n'
	
	password = jotools.get_param(req, 'password', None) 
	username = jotools.get_param(req, 'username', None)
	if username == None or password == None or not jotools.checkuname(username):
		joheaders.error_page(req,
		                 u"Käyttäjätunnus tai salasana puuttuu tai käyttäjätunnus on väärin")
		return '\n'
	
	pwhash = sha.new((_config.PW_SALT + password).encode('UTF-8')).hexdigest()
	db = jodb.connect_private()
	results = db.query(("select uid from appuser where uname = '%s' and pwhash = '%s' " +
	                    "and disabled = FALSE") % (username.encode('UTF-8'), pwhash))
	if results.ntuples() == 0:
		joheaders.error_page(req, u"Käyttäjätunnus tai salasana on väärin")
		return '\n'
	
	uid = results.getresult()[0][0]
	
	# Generate session key
	sesssha = sha.new()
	sesssha.update(username)
	sesssha.update(pwhash)
	if hasattr(os, 'urandom'): # this is only available in Python >= 2.4
		sesssha.update(os.urandom(15))
	else:
		sesssha.update(`time.time()`)
		sesssha.update(`random.random()`)
		sesssha.update(`os.times()`)
	sesskey = sesssha.hexdigest()
	
	db.query(("update appuser set session_key = '%s', session_exp = CURRENT_TIMESTAMP + " +
	          "interval '%i seconds' where uid = %i") % (sesskey, _config.SESSION_TIMEOUT, uid))
	if _config.WWW_ROOT_DIR == '': cookiepath = '/'
	else: cookiepath = _config.WWW_ROOT_DIR
	req.headers_out['Set-Cookie'] = 'session=%s; path=%s' % (sesskey, cookiepath)
	if wid == None: wid_n = 0
	else: wid_n = jotools.toint(wid)
	if wid_n != 0:
		joheaders.redirect_header(req, _config.WWW_ROOT_DIR + u"/word/edit?wid=%i" % wid_n)
	elif jotools.get_param(req, 'redir', None) != None:
		joheaders.redirect_header(req, _config.WWW_ROOT_DIR +
		                               jotools.get_param(req, 'redir', u''))
	else: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + u"/")
	return "</html>"

def logout(req, wid = None):
	if req.method != 'POST':
		joheaders.error_page(req, u"Vain POST-pyynnöt ovat sallittuja")
		return '\n'
	session = jotools.get_session(req)
	if session != '':
		db = jodb.connect_private()
		db.query(("update appuser set session_key = NULL, session_exp = NULL " +
		          "where session_key = '%s'") % session)
	req.headers_out['Set-Cookie'] = 'session=; path=%s; expires=Thu, 01-Jan-1970 00:00:01 GMT' \
	                                % _config.WWW_ROOT_DIR
	if wid == None: wid_n = 0
	else: wid_n = jotools.toint(wid)
	if wid_n == 0: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + u"/")
	else: joheaders.redirect_header(req, _config.WWW_ROOT_DIR + u"/word/edit?wid=%i" % wid_n)
	return "</html>"
