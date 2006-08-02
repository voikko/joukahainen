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
import random
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

# Writes a table body for entering new words. If words != None, the table is initialised with the given
# list of words. Otherwise empty list is written, with the number of rows taken from parameter 'count'.
def _add_entry_fields(req, db, words = None, count = 1):
	class_res = db.query("select classid, name from wordclass").getresult()
	if words == None:
		for i in range(count):
			jotools.write(req, u'<tr><td><input type="text" name="word%i" /></td><td>' % i)
			for res in class_res:
				jotools.write(req, (u'<label><input type="radio" name="class%i" ' +
				                     'value="%i">%s</input></label>\n') \
				            % (i, res[0], jotools.escape_html(unicode(res[1], 'UTF-8'))))
			jotools.write(req, u'</td></tr>\n')
		return
	i = 0
	for (oword, word, need_confirm, homonyms) in words:
		jotools.write(req, u'<tr><td>')
		if oword != None:
			jotools.write(req, u'<input type="hidden" name="origword%i" value=%s />' \
			                   % (i, jotools.escape_form_value(oword)))
		if need_confirm:
			jotools.write(req, u'<input type="hidden" name="word%i" value=%s />' \
			                   % (i, jotools.escape_form_value(word)))
			jotools.write(req, u'%s</td><td>' % jotools.escape_html(word))
		else:
			jotools.write(req, u'<input type="text" name="word%i" value=%s /></td><td>' \
			                   % (i, jotools.escape_form_value(word)))
			jotools.write(req, u'%s</td><td>' % jotools.escape_html(homonyms))
		for res in class_res:
			jotools.write(req, (u'<label><input type="radio" name="class%i" ' +
			                     'value="%i">%s</input></label>\n') \
			            % (i, res[0], jotools.escape_html(unicode(res[1], 'UTF-8'))))
		if oword != None:
			jotools.write(req, (u'<label><input type="radio" name="class%i" value=0>' +
			                    u'virheellinen sana</input></label>') % i)
		jotools.write(req, u'</td>')
		if need_confirm:
			jotools.write(req, u'<td><input type="checkbox" name="confirm%i"></td><td>' % i)
			jotools.write(req, homonyms)
			jotools.write(req, u'</td>')
		jotools.write(req, u'</tr>\n')
		i = i + 1

# Returns a list of links for all of the homonyms of given word.
def _list_homonyms(db, word):
	res = db.query(("SELECT w.wid, w.word, wc.name FROM word w, wordclass wc " +
		      "WHERE w.class = wc.classid AND w.word = '%s'") \
		      % jotools.escape_sql_string(word))
	h = u''
	for r in res.getresult():
		h = h + u'<a href="edit?wid=%i">%s(%s)</a> ' \
		    % (r[0], jotools.escape_html(unicode(r[1], 'UTF-8')),
		       jotools.escape_html(unicode(r[2], 'UTF-8')))
	return h

# Stores a new word into the database and marks the original in raw_words as processed
# (if needed). Returns (wid, add_entry_structure) where wid is the identifier for
# the new word (or None if nothing was added) and add_entry_structure is a tuple
# for _add_entry containing the description of a word that needs confirmation from
# user before being added (or None if no confirmation is needed).
def _store_word(db, word, oword, wclass, dupl_confirmed, uid):
	if wclass != 0:
		if not dupl_confirmed:
			hlist = _list_homonyms(db, word)
			if len(hlist) > 0: return (None, (oword, word, True, hlist))
		wid = db.query("SELECT nextval('word_wid_seq')").getresult()[0][0]
		db.query("INSERT INTO word(wid, word, class, cuser) VALUES(%i, '%s', %i, %i)" \
		         % (wid, jotools.escape_sql_string(word), wclass, uid))
	if oword != None:
		db.query("UPDATE raw_word SET processed = TRUE WHERE word = '%s'" \
		         % jotools.escape_sql_string(oword))
	if wclass == 0: return (None, None)
	else: return (wid, None)

def add(req, fromdb = None):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Ei oikeuksia tietojen muuttamiseen')
		return '\n'
	db = jodb.connect()
	words_per_page = 15
	if req.method == 'GET':
		class_res = db.query("select classid, name from wordclass").getresult()
		if fromdb == None: # Add words manually
			joheaders.list_page_header(req, u"Joukahainen &gt; Lisää sanoja", uid, uname)
			jotools.write(req, u'<form method="post" action="add">\n' +
			                   u'<table class="wadd">\n<tr><th>Sana</th><th>Sanaluokka</th></tr>\n')
			_add_entry_fields(req, db, None, words_per_page)
			jotools.write(req, u'</table>\n' +
			                   u'<p><input type="submit" value="Lisää sanoja"></p></form>\n')
			joheaders.list_page_footer(req)
			return '</html>\n'
		else: # Get words from the database
			category = jotools.get_param(req, 'category', None)
			if category == None: condition = ""
			else: condition = "AND coalesce(info, '') = '%s'" \
			                  % jotools.escape_sql_string(category)
			results = db.query("SELECT count(*) FROM raw_word WHERE processed = FALSE %s" \
			                   % condition)
			nwords = results.getresult()[0][0]
			if nwords <= words_per_page: limit = ""
			else: limit = "LIMIT %i OFFSET %i" % (words_per_page,
			              random.randint(0, nwords - words_per_page))
			results = db.query(("SELECT word, coalesce(notes, '') FROM raw_word " +
			                    "WHERE processed = FALSE %s " +
			                    "ORDER BY word %s") % (condition, limit))
			if results.ntuples() == 0 and category == None:
				joheaders.error_page(req, u'Tietokannassa ei ole lisäystä odottavia ' +
				          u'sanoja.')
				return '\n'
			if results.ntuples() == 0 and category != None:
				joheaders.error_page(req, u'Tietokannassa ei ole lisäystä odottavia ' +
				          u'sanoja kategoriassa %s.' % jotools.escape_html(category))
				return '\n'
			joheaders.list_page_header(req, u"Joukahainen &gt; Lisää sanoja", uid, uname)
			jotools.write(req, u'<form method="post" action="add">\n')
			jotools.write(req, u'<table class="wadd">\n')
			words = []
			for word in results.getresult():
				words.append((unicode(word[0], 'UTF-8'),
				              unicode(word[0], 'UTF-8'), False,
					    unicode(word[1], 'UTF-8')))
			_add_entry_fields(req, db, words, None)
			jotools.write(req, u'</table>\n' +
			                   u'<p><input type="submit" value="Lisää sanoja"></p></form>\n')
			joheaders.list_page_footer(req)
			return '</html>\n'
	if req.method != 'POST':
		joheaders.error_page(req, u'Vain GET/POST-pyynnöt ovat sallittuja')
		return '\n'
	db.query("BEGIN")
	if jotools.get_param(req, 'confirm', u'') == u'on': confirm = True
	else: confirm = False
	nwordlist = []
	added_count = 0
	need_confirm_count = 0
	i = -1
	while True:
		i = i + 1
		nword = jotools.get_param(req, 'word%i' % i, u'')
		if nword == u'': break
		nclass = jotools.toint(jotools.get_param(req, 'class%i' % i, u'-1'))
		oword = jotools.get_param(req, 'origword%i' % i, None)
		nclass = jotools.get_param(req, 'class%i' % i, None)
		if not nclass in [None, u'']: nclass = jotools.toint(nclass)
		else: continue
		if confirm and nclass != 0 and jotools.get_param(req, 'confirm%i' % i, u'') != u'on':
			continue
		new_item = _store_word(db, nword, oword, nclass, confirm, uid)
		if new_item[0] != None: added_count = added_count + 1
		if new_item[1] != None: need_confirm_count = need_confirm_count + 1
		nwordlist.append(new_item)
	db.query("COMMIT")
	if need_confirm_count > 0:
		joheaders.list_page_header(req, u'Joukahainen &gt; Lisää sanoja', uid, uname)
		jotools.write(req, u'<p>Ainakin osa lisäämistäsi sanoista on jo sanastossa. ' +
		              u'Aseta sanaluokka ja merkitse rastilla sanat, jotka haluat ' +
			    u'lisättäviksi tästä huolimatta ja yritä tallennusta uudelleen.</p>')
		jotools.write(req, u'<form method="post" action="add">\n')
		jotools.write(req, u'<table class="wadd"><tr><th>Sana</th><th>Sanaluokka</th><th>' +
		              u'Vahvista homonyymin lisäys</th><th>Homonyymit</th></tr>\n')
		words = []
		for word in nwordlist:
			if word[1] != None: words.append(word[1])
		_add_entry_fields(req, db, words, None)
		jotools.write(req, u'</table>\n<p>' +
		                   u'<input type="hidden" name="confirm" value="on">' +
		                   u'<input type="submit" value="Lisää sanoja"></p></form>\n')
		joheaders.list_page_footer(req)
		return '</html>\n'
	if added_count == 0:
		joheaders.page_header(req, u"Joukahainen &gt; Lisää sanoja")
		jotools.write(req, u'<p>Yhtään sanaa ei lisätty sanastoon. ' +
		                   u'<a href="..">Takaisin aloitussivulle ...</a></p>')
		joheaders.page_footer(req)
		joheaders.error_page(req, u'Yhtään sanaa ei lisätty')
		return '</html>\n'
	if added_count == 1:
		for n in nwordlist:
			if n[0] != None:
				joheaders.redirect_header(req, u'edit?wid=%i' % n[0])
				return '\n'
	# More than one word was added
	joheaders.page_header(req, u"Joukahainen &gt; Lisää sanoja")
	jotools.write(req, u'<p>Sanoja lisätty. <a href="..">Takaisin aloitussivulle ...</a></p>')
	joheaders.page_footer(req)
	return '</html>\n'

def categories(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, u'Ei oikeuksia tietojen muuttamiseen')
		return '\n'
	db = jodb.connect()
	results = db.query("SELECT coalesce(info, ''), count(*) FROM raw_word " +
	                   "WHERE processed = FALSE " +
	                   "GROUP BY coalesce(info, '') " +
	                   "ORDER BY coalesce(info, '') ")
	if results.ntuples() == 0:
		joheaders.error_page(req, u'Tietokannassa ei ole lisäystä odottavia sanoja.')
		return '\n'
	joheaders.list_page_header(req, u"Joukahainen &gt; Lisää sanoja", uid, uname)
	jotools.write(req, u"<p>Valitse kategoria, jonka sanoja haluat lisätä:</p>\n")
	jotools.write(req, u"<table><tr><th>Kategoria</th><th>Sanoja jäljellä</th></tr>\n")
	for result in results.getresult():
		cat = unicode(result[0], 'UTF-8')
		if cat == u'': cats = u'(ei kategoriaa)'
		else: cats = cat
		jotools.write(req, (u'<tr><td><a href="add?fromdb=1&amp;category=%s">%s</a></td>' +
		                    u'<td>%i</td></tr>\n') \
		  % (jotools.escape_url(cat), jotools.escape_html(cats), result[1]))
	jotools.write(req, u"</table>\n")
	jotools.write(req, u'<p><a href="add?fromdb=1">Kaikki sanat ...</a></p>\n')
	joheaders.list_page_footer(req)
	return '</html>\n'
