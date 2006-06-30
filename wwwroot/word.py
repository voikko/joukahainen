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
	if (wid == None):
		joheaders.error_page(req, u'Parametri wid on pakollinen')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, u'Sanaa %i ei ole\n' % wid_n)
		return '\n'
	joheaders.page_header(req)
	wordinfo = results.getresult()[0]
	(uid, uname, editable) = jotools.get_login_user(req)
	static_vars = {'WID': wid_n, 'WORD': unicode(wordinfo[0], 'UTF-8'), 'CLASSID': wordinfo[1],
	               'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
	jotools.process_template(req, db, static_vars, 'word_edit', 'fi', 'joeditors')
	joheaders.page_footer(req)
	return "</html>"

def change(req, wid = None):
	if req.method != 'POST':
		joheaders.error_page(req, u'Vain POST-pyynnöt ovat sallittuja')
		return '\n'
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Ei oikeuksia tietojen muuttamiseen')
		return '\n'
	if (wid == None):
		joheaders.error_page(req, u'Parametri wid on pakollinen')
		return '\n'
	
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	db.query("begin")
	wclass_results = db.query("select class from word where wid = %i" % wid_n)
	if wclass_results.ntuples() == 0:
		joheaders.error_page(req, u'Sanaa %i ei ole\n' % wid_n)
		db.query("rollback")
		return '\n'
	wclass = wclass_results.getresult()[0][0]
	edfield_results = db.query(("select a.type, a.aid, a.descr from attribute a, attribute_class ac " +
	                            "where a.aid = ac.aid and ac.classid = %i and a.editable = TRUE") % wclass)
	eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
	event_inserted = False
	messages = []
	
	for attribute in edfield_results.getresult():
		if attribute[0] == 1: # string attribute
			html_att = 'string%i' % attribute[1]
			newval = None
			for field in req.form.list:
				if field.name == html_att:
					newval = jotools.decode_form_value(field.value)
					break
			if newval == None: continue
			vresults = db.query(("select s.value from string_attribute_value s where " +
			                     "s.wid = %i and s.aid = %i") % (wid_n, attribute[1]))
			if vresults.ntuples() == 0: oldval = u""
			else: oldval = unicode(vresults.getresult()[0][0], 'UTF-8')
			if oldval == newval: continue
			if not event_inserted:
				db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
				         (eid, wid_n, uid))
				event_inserted = True
			if newval == u'':
				db.query(("delete from string_attribute_value where wid = %i " +
				          "and aid = %i") % (wid_n, attribute[1]))
			elif oldval == u'':
				db.query(("insert into string_attribute_value(wid, aid, value, eevent) " +
				          "values(%i, %i, '%s', %i)") % (wid_n, attribute[1],
					                        jotools.escape_sql_string(newval), eid))
			else:
				db.query(("update string_attribute_value set value='%s', eevent=%i " +
				          "where wid=%i and aid=%i") %
					(jotools.escape_sql_string(newval), eid, wid_n, attribute[1]))
			messages.append(u"%s: '%s' -> '%s'" % (unicode(attribute[2], 'UTF-8'),
			                oldval, newval))
	
	if event_inserted:
		mess_str = jotools.escape_sql_string(reduce(lambda x, y: x + u"\n" + y, messages, u""))
		db.query("update event set message = '%s' where eid = %i" % (mess_str, eid))
	db.query("commit")
	joheaders.redirect_header(req, u'edit?wid=%i' % wid_n)
	return '\n'
