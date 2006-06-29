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

# This file contains general helper functions

import codecs
import re
import Cookie
import time
import urllib
import jodb
import _config

def _call_handler(db, module, funcname, paramlist):
	if module == 'joeditors':
		import joeditors
		return joeditors.call(db, funcname, paramlist)
	if module == 'joindex':
		import joindex
		return joindex.call(db, funcname, paramlist)
	return u"Error: unknown module"

def toint(string):
	if string.isdigit(): return int(string)
	else: return 0

WCHARS = u"abcdefghijklmnopqrstuvwxyzåäöszèéABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖŠŽÈÉ-'|"
# Checks if string looks like a valid word
def checkword(string):
	for c in string:
		if not c in WCHARS: return False
	return True

UNAMECHARS = u'abcdefghijklmnopqrstuvwxyz'
# Checks if string looks like a valid user name
def checkuname(string):
	for c in string:
		if not c in UNAMECHARS: return False
	return True

def write(req, string):
	req.write(string.encode("UTF-8"))

def errormsg(req, error):
	write(req, error)

def process_template(req, db, static_vars, template_name, lang, module):
	tmplfilename = _config.TEMPLATE_PATH + '/' + template_name + '_' + lang + '.txt'
	tmplfile = codecs.open(tmplfilename, 'r', 'utf-8')
	var_re = re.compile("^(.*)\\$\\$(.*)\\$\\$(.*)$")
	func_re = re.compile("^(.*)\\((.*)\\)$")
	file_cont = True
	while file_cont:
		# FIXME: only one variable/function allowed on one line
		line = tmplfile.readline()
		file_cont = line.endswith('\n')
		var_match = var_re.match(line)
		if var_match != None:
			write(req, var_match.group(1))
			func_match = func_re.match(var_match.group(2))
			if func_match == None:
				write(req, unicode(static_vars[var_match.group(2)]))
			else:
				paramlist = []
				for param in func_match.group(2).split(','):
					param = param.strip()
					if param == '':
						paramlist.append(None)
					elif param[0] in '0123456789':
						paramlist.append(int(param))
					else:
						paramlist.append(static_vars[param])
				retstr = _call_handler(db, module, func_match.group(1), paramlist)
				write(req, retstr)
			write(req, var_match.group(3) + u'\n')
		else:
			write(req, line)
	tmplfile.close()

# Returns the session key of the request or '' if the key was not set or it is malformed
def get_session(req):
	if req.headers_in.has_key('Cookie'):
		c = Cookie.SimpleCookie()
		c.load(req.headers_in['Cookie'])
		if c.has_key('session'):
			sess = c['session'].value
			if len(sess) != 40: return ''
			for ch in sess:
				if not ch in '0123456789abcdef': return ''
			return sess
	return ''

# Returns (uid, uname, can_edit) or (None, None, False) if user is not properly logged in.
# Calling this function also refreshes the current session.
def get_login_user(req):
	session = get_session(req)
	if session == '': return (None, None, False)
	db = jodb.connect_private()
	results = db.query(("select uid, uname from appuser where session_key = '%s' " +
	                   "and session_exp > CURRENT_TIMESTAMP") % session)
	if results.ntuples() != 1: return (None, None, False)
	result = results.getresult()[0]
	db.query("update appuser set session_exp = CURRENT_TIMESTAMP + interval '%i seconds' where uid = %i" \
	         % (_config.SESSION_TIMEOUT, result[0]))
	return (result[0], unicode(result[1], 'UTF-8'), True)

# Converts a string to a form that is suitable for use as a value of the value attribute in html form elements
def escape_form_value(string):
	return urllib.quote_plus(string)

# Converts an unicode string to a form that is suitable for use in a SQL statement
def escape_sql_string(string):
	return string.replace(u"'", u"''").encode('UTF-8')
