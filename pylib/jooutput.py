# -*- coding: utf-8 -*-

# Copyright 2006 - 2008 Harri Pitkänen (hatapitk@iki.fi)
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

# This file contains functions for listing search results in different formats

import joheaders
import jotools
import jodb
import _config
import _apply_config

_ = _apply_config.translation.ugettext

def _print_html_line(db, wid, word, wclass):
	results = db.query("SELECT wid FROM flag_attribute_value WHERE aid in (24, 26)" +
	                "AND wid = %i" % wid)
	line = "<tr"
	if results.ntuples() > 0: line = line + " class='deleted'"
	line = line + "><td><a href='../word/edit?wid=%i'>%s</a></td><td>%s</td></tr>\n" \
	       % (wid, word, wclass)
	return line

def _html(req, db, query):
	offset_s = `jotools.toint(jotools.get_param(req, 'offset', u'0'))`
	limit_s = `jotools.toint(jotools.get_param(req, 'limit', u'200'))`
	if limit_s == u'0': limit_s = u'ALL'
	
	param_s = u''
	for field in req.form.list:
		if not field.name in ['limit', 'offset'] and jotools.checkid(field.name):
			param_s = param_s + field.name + u'=' + jotools.get_param(req, field.name, u'') + u'&'
	
	results = db.query("%s LIMIT %s OFFSET %s" % (query, limit_s, offset_s))
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u'No matching words were found'))
		return "\n"
	elif results.ntuples() == 1:
		joheaders.redirect_header(req, _config.WWW_ROOT_DIR + "/word/edit?wid=%i" \
		                               % results.getresult()[0][0])
		return "\n"
	else:
		(uid, uname, editable) = jotools.get_login_user(req)
		joheaders.page_header_navbar_level1(req, _('Search results'), uid, uname)
		jotools.write(req, u'<table><tr><th>%s</th><th>%s</th></tr>\n' \
		                   % (_("Word"), _("Word class")))
		for result in results.getresult():
			jotools.write(req, _print_html_line(db, result[0],
			              unicode(result[1], 'UTF-8'),
				    unicode(result[2], 'UTF-8')))
		jotools.write(req, u"</table>\n")
		if not limit_s == u'ALL' and results.ntuples() == jotools.toint(limit_s):
			jotools.write(req, (u'<p><a href="wlist?%soffset=%i&limit=%s">' +
			              u"%s ...</a></p>\n") % (param_s, int(offset_s)+int(limit_s),
				    limit_s, _(u'More results')))	
	joheaders.page_footer_plain(req)
	return '\n'

def call(req, outputtype, query):
	db = jodb.connect()
	if outputtype == 'html':
		_html(req, db, query)
	else:
		_apply_config.jooutput_call(req, outputtype, db, query)

def list_supported_types():
	types = []
	types.append(('html', _('Output as page with links')))
	langtypes = _apply_config.jooutput_list_supported_types()
	return types + langtypes
