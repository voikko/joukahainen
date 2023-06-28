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

# This file contains general helper functions

import codecs
import re
import http.cookies
import time
import urllib.request, urllib.parse, urllib.error
import gettext
import jodb
import joheaders
import _pg
import _config
from functions import checkword
from xml.sax import saxutils
from flask import request, Response
from io import StringIO

HTTP_MOVED_PERMANENTLY = 301

_ = gettext.gettext

def _call_handler(db, module, funcname, paramlist):
	if module == 'joeditors':
		import joeditors
		return joeditors.call(db, funcname, paramlist)
	if module == 'joindex':
		import joindex
		return joindex.call(db, funcname, paramlist)
	return _("Error: unknown module")

def toint(string):
	if string.isdigit(): return int(string)
	else: return 0

# Checks if string is safe to be used as a Posix regular expression
RECHARS = "abcdefghijklmnoôpqrstuüvwxyzåäöszèéšžáàóâABCDEFGHIJKLMNOÔPQRSTUÜVWXYZÅÄÖŠŽÈÉŠŽµΩΩ-'|_%*()[]+.:?$^"
def checkre(string):
	for c in string:
		if not c in RECHARS: return False
	return True

# Performs basic validity check for a Posix regular expression, replacing certain captial letters
# with useful character classes to simplify searching. If the expression is not valid, returns
# None
def expandre(string):
	if not checkre(string): return None
	string = string.replace('V', '(?:a|e|i|o|u|y|ä|ö|é|è|á|à|ó|ô|â)')
	string = string.replace('C', '(?:b|c|d|f|g|h|j|k|l|m|n|p|q|r|s|t|v|w|x|z|š|ž)')
	string = string.replace('A', '(?:a|ä)')
	string = string.replace('O', '(?:o|ö)')
	string = string.replace('U', '(?:u|y)')
	return string

UNAMECHARS = 'abcdefghijklmnopqrstuvwxyz'
# Checks if string looks like a valid user name
def checkuname(string):
	for c in string:
		if not c in UNAMECHARS: return False
	return True

IDCHARS = 'abcdefghijklmnopqrstuvwxyz'
# Checks if string looks like a valid identifier
def checkid(string):
	if len(string) == 0: return False
	if not string[0] in IDCHARS: return False
	for c in string:
		if not c in IDCHARS and not c in '1234567890': return False
	return True

def write(req, string):
	req.write(string)

def errormsg(req, error):
	write(req, error)

# Get a mapping from attribute ids to matching word class ids
def word_classes_for_attributes(db):
	results = db.query("SELECT aid, classid FROM attribute_class")
	cattributes = {}
	for row in results.getresult():
		aid = row[0]
		typeid = row[1]
		if aid not in cattributes:
			cattributes[aid] = set([])
		cattributes[aid].add(typeid)
	return cattributes

# Processes the given page template and writes the content to request req
def process_template(req, db, static_vars, template_name, lang, module, level):
	tmplfilename = _config.INSTALLATION_DIRECTORY + '/langpacks/' + \
	               lang + '/' + template_name + '.txt'
	tmplfile = codecs.open(tmplfilename, 'r', 'utf-8')
	var_re = re.compile("^(.*)\\$\\$(.*)\\$\\$(.*)$")
	func_re = re.compile("^(.*)\\((.*)\\)$")
	file_cont = True
	first_line = True
	cattributes = None
	while file_cont:
		# FIXME: only one variable/function allowed on one line
		line = tmplfile.readline()
		file_cont = line.endswith('\n')
		
		if line == "@BEGIN IF_EDIT_ALLOWED\n":
			if 'EDITABLE' not in static_vars or not static_vars['EDITABLE']:
				while line.endswith('\n') and line != "@END IF_EDIT_ALLOWED\n": line = tmplfile.readline()
			continue
		if line == "@END IF_EDIT_ALLOWED\n": continue
		
		if line.startswith("@BEGIN ATTRIBUTE_ENCLOSURE "):
			if cattributes is None:
				cattributes = word_classes_for_attributes(db)
			aid = int(line[27:].strip())
			if static_vars['CLASSID'] not in cattributes[aid]:
				while line.endswith('\n') and line != "@END ATTRIBUTE_ENCLOSURE\n": line = tmplfile.readline()
			continue
		if line == "@END ATTRIBUTE_ENCLOSURE\n": continue

		var_match = var_re.match(line)
		line_str = ''
		if var_match != None:
			line_str = line_str + var_match.group(1)
			func_match = func_re.match(var_match.group(2))
			if func_match == None:
				line_str = line_str + str(static_vars[var_match.group(2)])
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
				line_str = line_str + retstr
			line_str = line_str + var_match.group(3) + '\n'
		else:
			line_str = line_str + line
		if first_line:
			if 'UID' in static_vars: uid = static_vars['UID']
			else: uid = 0
			if 'UNAME' in static_vars: uname = static_vars['UNAME']
			else: uname = 0
			if 'WID' in static_vars: wid = static_vars['WID']
			else: wid = 0
			if level == 0:
				joheaders.page_header_navbar_level0(req, line_str.strip(),
				                                    uid, uname)
			if level == 1:
				joheaders.page_header_navbar_level1(req, line_str.strip(),
				                                    uid, uname, wid)
			first_line = False
		else: write(req, line_str)
	tmplfile.close()

# Returns the session key of the request or '' if the key was not set or it is malformed
def get_session(req):
	if 'Cookie' in req.headers_in:
		c = http.cookies.SimpleCookie()
		c.load(req.headers_in['Cookie'])
		if 'session' in c:
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
	results = db.query(("select uid, uname, isadmin from appuser where session_key = '%s' " +
	                   "and session_exp > CURRENT_TIMESTAMP") % session)
	if results.ntuples() != 1: return (None, None, False)
	result = results.getresult()[0]
	if result[2] == 'f' and _config.ONLY_ADMIN_LOGIN_ALLOWED: return (None, None, False)
	
	db.query("update appuser set session_exp = CURRENT_TIMESTAMP + interval '%i seconds' where uid = %i" \
	         % (_config.SESSION_TIMEOUT, result[0]))
	return (result[0], str(result[1], 'UTF-8'), True)

# Returns True, if given user is an administrator
def is_admin(uid):
	if uid == None: return False
	db = jodb.connect_private()
	results = db.query("SELECT isadmin FROM appuser WHERE uid = %i AND isadmin = TRUE" % uid)
	if results.ntuples() == 1: return True
	return False

# Converts a string to a form that is suitable for use as a value of the value attribute in html form elements
def escape_form_value(string):
	return saxutils.quoteattr(string)

# Converts a string to a form that is suitable for use in a URL
# The input should be ordinary (not Unicode) string
def escape_url(string):
	return urllib.parse.quote_plus(string)

# Converts a string to a form that is suitable for use in html document text
def escape_html(string):
	return saxutils.escape(string)

# Converts an unicode string to a form that is suitable for use in a SQL statement
def escape_sql_string(string):
	return str(_pg.escape_string(string.encode('UTF-8')), 'UTF-8')

# Returns a list that has all unique elements of the argument list. The returned list is sorted
# according to element values. The original list must be sortable
def unique(oldlist):
	if len(oldlist) == 0: return []
	oldlist.sort()
	lastelem = oldlist[0]
	newlist = [lastelem]
	for elem in oldlist[1:]:
		if elem != lastelem:
			lastelem = elem
			newlist.append(lastelem)
	return newlist

# Returns the value of given request parameter or default if parameter is not set
def get_param(req, name, default):
	if request.method == 'POST':
		return request.form.get(name, default)
	return request.args.get(name, default)

# Returns the integer prefix of the given string or 0, if no such prefix was found
def integer_prefix(string):
	i = 0
	while i < len(string) and string[i].isdigit(): i = i + 1
	if i == 0: return (0, 0)
	elif i == len(string): return (i, int(string))
	else: return (i, int(string[0:i]))

# Returns a link matching the given comment string
def _comment_link(comment):
	if comment.startswith('('):
		leading_chars = 1
		lead = '('
	else:
		leading_chars = 0
		lead = ''
	cstr = comment[leading_chars:]
	if cstr.startswith('#'):
		(nlen, wid) = integer_prefix(cstr[1:])
		if nlen == 0: return comment
		return lead + '<a href="%s/word/edit?wid=%i">%s</a>' \
		       % (_config.WWW_ROOT_DIR, wid, cstr[:nlen+1]) \
		       + cstr[nlen+1:]
	elif cstr.startswith('wid#'):
		(nlen, wid) = integer_prefix(cstr[4:])
		if nlen == 0: return comment
		return lead + '<a href="%s/word/edit?wid=%i">%s</a>' \
		       % (_config.WWW_ROOT_DIR, wid, cstr[:nlen+4]) \
		       + cstr[nlen+4:]
	else: return comment

# Turn special identifiers in word comments into links
def comment_links(comment):
	comment_parts = comment.split()
	newcomment = ''
	for part in comment_parts:
		newcomment = newcomment + _comment_link(part) + ' '
	return newcomment

class Request_wrapper:
	def __init__(self):
		self.content = StringIO()
		self.status = 200
		self.headers_in = request.headers
		self.headers_out = {}
		self.content_type = "text/html; charset=UTF-8"
	
	def write(self, text):
		self.content.write(text)
	
	def response(self):
		resp = Response(self.content.getvalue(), status=self.status, mimetype=self.content_type)
		for key, value in self.headers_out.items():
			resp.headers[key] = value
		return resp
