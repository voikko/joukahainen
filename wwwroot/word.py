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
			newval = jotools.get_param(req, html_att, None)
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
	
	comment = jotools.get_param(req, 'comment', u'')
	
	if comment != u'':
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		db.query("update event set comment = '%s' where eid = %i" \
		         % (jotools.escape_sql_string(comment), eid))
	if event_inserted and len(messages) > 0:
		mess_str = jotools.escape_sql_string(reduce(lambda x, y: x + u"\n" + y, messages, u""))
		db.query("update event set message = '%s' where eid = %i" % (mess_str, eid))
	db.query("commit")
	joheaders.redirect_header(req, u'edit?wid=%i' % wid_n)
	return '\n'

def flags(req, wid = None):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Muokkausoikeus puuttuu')
		return '\n'
	if wid == None:
		joheaders.error_page(req, u'Parametri wid on pakollinen')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, u'Sanaa %i ei ole\n' % wid_n)
		return '\n'
	wordinfo = results.getresult()[0]
	if req.method == 'GET': # show editor
		static_vars = {'WID': wid_n, 'WORD': unicode(wordinfo[0], 'UTF-8'), 'CLASSID': wordinfo[1],
		               'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
		jotools.process_template(req, db, static_vars, 'word_flags', 'fi', 'joeditors')
		joheaders.page_footer(req)
		return "</html>"
	if req.method != 'POST':
		joheaders.error_page(req, u'Vain GET/POST-pyynnöt ovat sallittuja')
		return '\n'
	db.query("begin")
	edfield_results = db.query(("SELECT a.aid, a.descr, CASE WHEN fav.wid IS NULL THEN 'f' ELSE 't' END " +
	                    "FROM attribute_class ac, attribute a " +
	                    "LEFT OUTER JOIN flag_attribute_value fav ON (a.aid = fav.aid and fav.wid = %i) " +
	                    "WHERE a.aid = ac.aid AND ac.classid = %i AND a.type = 2" +
	                    "ORDER BY a.descr") % (wid_n, wordinfo[1]))
	eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
	event_inserted = False
	messages = []
	
	for attribute in edfield_results.getresult():
		html_att = 'attr%i' % attribute[0]
		if jotools.get_param(req, html_att, u'') == u'on': newval = True
		else: newval = False
		
		if attribute[2] == 't': oldval = True
		else: oldval = False
		
		if oldval == newval: continue
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		if newval == False:
			db.query(("delete from flag_attribute_value where wid = %i " +
			          "and aid = %i") % (wid_n, attribute[0]))
			messages.append(u"Lippu poistettu: '%s'" % unicode(attribute[1], 'UTF-8'))
		if newval == True:
			db.query(("insert into flag_attribute_value(wid, aid, eevent) " +
			          "values(%i, %i, %i)") % (wid_n, attribute[0], eid))
			messages.append(u"Lippu lisätty: '%s'" % unicode(attribute[1], 'UTF-8'))
	
	comment = jotools.get_param(req, 'comment', u'')
	
	if comment != u'':
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		db.query("update event set comment = '%s' where eid = %i" \
		         % (jotools.escape_sql_string(comment), eid))
	if event_inserted and len(messages) > 0:
		mess_str = jotools.escape_sql_string(reduce(lambda x, y: x + u"\n" + y, messages, u""))
		db.query("update event set message = '%s' where eid = %i" % (mess_str, eid))
	db.query("commit")
	joheaders.redirect_header(req, u'edit?wid=%i' % wid_n)
	return '\n'

def rwords(req, wid = None):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Muokkausoikeus puuttuu')
		return '\n'
	if wid == None:
		joheaders.error_page(req, u'Parametri wid on pakollinen')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, u'Sanaa %i ei ole\n' % wid_n)
		return '\n'
	wordinfo = results.getresult()[0]
	if req.method == 'GET': # show editor
		static_vars = {'WID': wid_n, 'WORD': unicode(wordinfo[0], 'UTF-8'), 'CLASSID': wordinfo[1],
		               'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
		jotools.process_template(req, db, static_vars, 'word_rwords', 'fi', 'joeditors')
		joheaders.page_footer(req)
		return "</html>"
	if req.method != 'POST':
		joheaders.error_page(req, u'Vain GET/POST-pyynnöt ovat sallittuja')
		return '\n'
	db.query("begin")
	rword_results = db.query("SELECT rwid, related_word FROM related_word WHERE wid = %i" % wid_n)
	rword_res = rword_results.getresult()
	eid = db.query("select nextval('event_eid_seq')").getresult()[0][0]
	event_inserted = False
	messages = []
	
	for attribute in rword_res:
		html_att = 'rword%i' % attribute[0]
		if jotools.get_param(req, html_att, u'') == u'on': remove = True
		else: remove = False
		
		if not remove: continue
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		db.query(("delete from related_word where wid = %i and rwid = %i") % (wid_n, attribute[0]))
		messages.append(u"Kirjoitusasu poistettu: '%s'" % unicode(attribute[1], 'UTF-8'))
	
	newwords = jotools.get_param(req, 'add', u'')
	for word in jotools.unique(newwords.split()):
		if not jotools.checkword(word): continue
		already_listed = False
		for attribute in rword_res:
			if word == unicode(attribute[1], 'UTF-8'): 
				already_listed = True
				break
		if already_listed: continue
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		db.query("insert into related_word(wid, eevent, related_word) values(%i, %i, '%s')" \
		         % (wid_n, eid, jotools.escape_sql_string(word)))
		messages.append(u"Kirjoitusasu lisätty: '%s'" % word)
	
	comment = jotools.get_param(req, 'comment', u'')
	
	if comment != u'':
		if not event_inserted:
			db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
			         (eid, wid_n, uid))
			event_inserted = True
		db.query("update event set comment = '%s' where eid = %i" \
		         % (jotools.escape_sql_string(comment), eid))
	if event_inserted and len(messages) > 0:
		mess_str = jotools.escape_sql_string(reduce(lambda x, y: x + u"\n" + y, messages, u""))
		db.query("update event set message = '%s' where eid = %i" % (mess_str, eid))
	db.query("commit")
	joheaders.redirect_header(req, u'edit?wid=%i' % wid_n)
	return '\n'

def add(req, fromdb = None):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Ei oikeuksia tietojen muuttamiseen')
		return '\n'
	db = jodb.connect()
	if req.method == 'GET':
		class_res = db.query("select classid, name from wordclass").getresult()
		if fromdb == None:
			joheaders.list_page_header(req, u"Joukahainen &gt; Lisää sana", uid, uname)
			jotools.write(req, u'<form method="post" action="add">\n' + \
			              u'<p><label>Sana: <input type="text" name="word" /></label>\n')
			for res in class_res:
				jotools.write(req, (u'<label><input type="radio" name="class" ' +
				                     'value="%i">%s</input></label>\n') \
				              % (res[0], jotools.escape_html(unicode(res[1], 'UTF-8'))))
			jotools.write(req, u'</p><p><input type="submit" value="Lisää sana"></p></form>\n')
			joheaders.list_page_footer(req)
			return '</html>\n'
		# TODO: add from raw_word
	if req.method != 'POST':
		joheaders.error_page(req, u'Vain GET/POST-pyynnöt ovat sallittuja')
		return '\n'
	if fromdb == None:
		nword = jotools.get_param(req, 'word', u'')
		if nword == u'':
			joheaders.error_page(req, u'Lisättävä sana on pakollinen')
			return '\n'
		if not jotools.checkword(nword):
			joheaders.error_page(req, u'Lisättävässä sanassa on vääriä merkkejä')
			return '\n'
		nclass = jotools.toint(jotools.get_param(req, 'class', u'0'))
		if nclass == 0:
			joheaders.error_page(req, u'Uusi sana pitää laittaa oikeaan luokkaan')
			return '\n'
		db.query("begin")
		wid = db.query("select nextval('word_wid_seq')").getresult()[0][0]
		db.query("insert into word(wid, word, class, cuser) values(%i, '%s', %i, %i)" \
		         % (wid, jotools.escape_sql_string(nword), nclass, uid))
		db.query("commit")
		joheaders.redirect_header(req, u'edit?wid=%i' % wid)
		return '\n'
	# TODO: add from raw_word
