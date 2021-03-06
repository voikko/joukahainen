# -*- coding: utf-8 -*-

# Copyright 2006 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains user administration functions

from mod_python import apache
from _pg import ProgrammingError

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

_ = _apply_config.translation.ugettext

def login(req, wid = None):
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only POST requests are allowed'))
		return '\n'
	
	password = jotools.get_param(req, 'password', None) 
	username = jotools.get_param(req, 'username', None)
	if username == None or password == None or not jotools.checkuname(username):
		joheaders.error_page(req,
		                 _(u"Missing or incorrect username or password"))
		return '\n'
	
	pwhash = sha.new((_config.PW_SALT + password).encode('UTF-8')).hexdigest()
	db = jodb.connect_private()
	results = db.query(("select uid, isadmin from appuser where uname = '%s' and pwhash = '%s' " +
	                    "and disabled = FALSE") % (username.encode('UTF-8'), pwhash))
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u"Incorrect username or password"))
		return '\n'
	
	(uid, isadmin) = results.getresult()[0]
	if isadmin == 'f' and _config.ONLY_ADMIN_LOGIN_ALLOWED:
		joheaders.error_page(req, _(u"Only administrator logins are allowed at the moment"))
		return '\n'
	
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
		joheaders.error_page(req, _(u'Only POST requests are allowed'))
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

def addform(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not jotools.is_admin(uid):
		joheaders.error_page(req, _(u'You must be an administrator to do this'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _(u'Add user'), uid, uname)
	jotools.write(req, u'''
<form method="post" action="add">
<table>
<tr><td>%s</td><td><input type="text" name="firstname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="lastname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="uname" /></td></tr>
<tr><td>%s</td><td><input type="text" name="email" /></td></tr>
<tr><td>%s</td><td><input type="text" name="passwd" /></td></tr>
</table>
<input type="submit" value="%s" />
</form>
'''        % (_(u'First name'), _(u'Last name'), _(u'Username'), _(u'Email address'),
              _(u'Password'), _(u'Add user')))
	joheaders.page_footer_plain(req)
	return '\n'

def add(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not jotools.is_admin(uid):
		joheaders.error_page(req, _(u'You must be an administrator to do this'))
		return '\n'
	datafields = ['firstname', 'lastname', 'uname', 'email', 'passwd']
	values = {}
	for datafield in datafields:
		values[datafield] = jotools.get_param(req, datafield, u'')
		if datafield != 'passwd':
			values[datafield] = jotools.escape_sql_string(values[datafield])
		if datafield not in ['email', 'passwd'] and values[datafield] == '':
			joheaders.error_page(req, _(u'Required field %s is missing') % datafield)
			return '\n'
	if values['passwd'] == u'':
		joheaders.error_page(req, _(u'Required field %s is missing') % u'passwd')
		return '\n'
	pwhash = sha.new((_config.PW_SALT + values['passwd']).encode('UTF-8')).hexdigest()
	privdb = jodb.connect_private()
	newuid = privdb.query("SELECT nextval('appuser_uid_seq')").getresult()[0][0]
	try:
		privdb.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email, pwhash)" +
		              "VALUES(%i, '%s', '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
			    values['firstname'], values['lastname'], values['email'], pwhash))
	except ProgrammingError:
		joheaders.error_page(req, _(u'User name is already in use'))
		return '\n'
	db = jodb.connect()
	db.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email)" +
	          "VALUES(%i, '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
		values['firstname'], values['lastname'], values['email']))
	joheaders.ok_page(req, _(u'New user was added succesfully'))
	return '\n'

def passwdform(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if uid == None:
		joheaders.error_page(req, _(u'You must be logged in to do this'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _(u'Change password'), uid, uname)
	jotools.write(req, u'''
<form method="post" action="changepasswd">
<table>
<tr><td>%s</td><td><input type="password" name="oldpw" /></td></tr>
<tr><td>%s</td><td><input type="password" name="newpw" /></td></tr>
</table>
<input type="submit" value="%s" />
</form>
'''        % (_(u'Old password'), _(u'New password'), _(u'Change password')))
	joheaders.page_footer_plain(req)
	return '\n'

def changepasswd(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if uid == None:
		joheaders.error_page(req, _(u'You must be logged in to do this'))
		return '\n'
	oldpw = jotools.get_param(req, 'oldpw', u'')
	newpw = jotools.get_param(req, 'newpw', u'')
	if oldpw == u'' or newpw == u'':
		joheaders.error_page(req, _(u'Required field is missing'))
		return '\n'
	oldpwhash = sha.new((_config.PW_SALT + oldpw).encode('UTF-8')).hexdigest()
	db = jodb.connect_private()
	results = db.query(("select uid from appuser where uid = %i and pwhash = '%s'") \
	                   % (uid, oldpwhash))
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u"Incorrect old password"))
		return '\n'
	newpwhash = sha.new((_config.PW_SALT + newpw).encode('UTF-8')).hexdigest()
	db.query("update appuser set pwhash = '%s' where uid = %i" % (newpwhash, uid))
	joheaders.ok_page(req, _(u'Password was changed succesfully'))
	return '\n'
