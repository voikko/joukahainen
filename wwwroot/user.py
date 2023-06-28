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

def addform(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not jotools.is_admin(uid):
		joheaders.error_page(req, _('You must be an administrator to do this'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _('Add user'), uid, uname)
	jotools.write(req, '''
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
'''        % (_('First name'), _('Last name'), _('Username'), _('Email address'),
              _('Password'), _('Add user')))
	joheaders.page_footer_plain(req)
	return '\n'

def add(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not jotools.is_admin(uid):
		joheaders.error_page(req, _('You must be an administrator to do this'))
		return '\n'
	datafields = ['firstname', 'lastname', 'uname', 'email', 'passwd']
	values = {}
	for datafield in datafields:
		values[datafield] = jotools.get_param(req, datafield, '')
		if datafield != 'passwd':
			values[datafield] = jotools.escape_sql_string(values[datafield])
		if datafield not in ['email', 'passwd'] and values[datafield] == '':
			joheaders.error_page(req, _('Required field %s is missing') % datafield)
			return '\n'
	if values['passwd'] == '':
		joheaders.error_page(req, _('Required field %s is missing') % 'passwd')
		return '\n'
	pwhash = sha.new((_config.PW_SALT + values['passwd']).encode('UTF-8')).hexdigest()
	privdb = jodb.connect_private()
	newuid = privdb.query("SELECT nextval('appuser_uid_seq')").getresult()[0][0]
	try:
		privdb.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email, pwhash)" +
		              "VALUES(%i, '%s', '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
			    values['firstname'], values['lastname'], values['email'], pwhash))
	except ProgrammingError:
		joheaders.error_page(req, _('User name is already in use'))
		return '\n'
	db = jodb.connect()
	db.query(("INSERT INTO appuser(uid, uname, firstname, lastname, email)" +
	          "VALUES(%i, '%s', '%s', '%s', '%s')") % (newuid, values['uname'],
		values['firstname'], values['lastname'], values['email']))
	joheaders.ok_page(req, _('New user was added succesfully'))
	return '\n'

def passwdform(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if uid == None:
		joheaders.error_page(req, _('You must be logged in to do this'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _('Change password'), uid, uname)
	jotools.write(req, '''
<form method="post" action="changepasswd">
<table>
<tr><td>%s</td><td><input type="password" name="oldpw" /></td></tr>
<tr><td>%s</td><td><input type="password" name="newpw" /></td></tr>
</table>
<input type="submit" value="%s" />
</form>
'''        % (_('Old password'), _('New password'), _('Change password')))
	joheaders.page_footer_plain(req)
	return '\n'

def changepasswd(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if uid == None:
		joheaders.error_page(req, _('You must be logged in to do this'))
		return '\n'
	oldpw = jotools.get_param(req, 'oldpw', '')
	newpw = jotools.get_param(req, 'newpw', '')
	if oldpw == '' or newpw == '':
		joheaders.error_page(req, _('Required field is missing'))
		return '\n'
	oldpwhash = sha.new((_config.PW_SALT + oldpw).encode('UTF-8')).hexdigest()
	db = jodb.connect_private()
	results = db.query(("select uid from appuser where uid = %i and pwhash = '%s'") \
	                   % (uid, oldpwhash))
	if results.ntuples() == 0:
		joheaders.error_page(req, _("Incorrect old password"))
		return '\n'
	newpwhash = sha.new((_config.PW_SALT + newpw).encode('UTF-8')).hexdigest()
	db.query("update appuser set pwhash = '%s' where uid = %i" % (newpwhash, uid))
	joheaders.ok_page(req, _('Password was changed succesfully'))
	return '\n'
