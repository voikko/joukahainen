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

# This file contains the word editor

from mod_python import apache

import sys
import random
import _apply_config
import _config
import joheaders
import jotools
import joeditors
import jodb

_ = _apply_config.translation.ugettext

def edit(req, wid = None):
	if (wid == None):
		joheaders.error_page(req, _(u'Parameter %s is required') % u'wid')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u'Word %i does not exist') % wid_n)
		return '\n'
	wordinfo = results.getresult()[0]
	(uid, uname, editable) = jotools.get_login_user(req)
	static_vars = {'WID': wid_n, 'WORD': unicode(wordinfo[0], 'UTF-8'), 'CLASSID': wordinfo[1],
	               'UID': uid, 'UNAME': uname, 'EDITABLE': editable}
	jotools.process_template(req, db, static_vars, u'word_edit', _config.LANG, u'joeditors', 1)
	joheaders.page_footer_plain(req)
	return '\n'

def change(req, wid = None):
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only POST requests are allowed'))
		return '\n'
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if (wid == None):
		joheaders.error_page(req, _(u'Parameter %s is required') % u'wid')
		return '\n'
	
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	db.query("begin")
	wclass_results = db.query("select class from word where wid = %i" % wid_n)
	if wclass_results.ntuples() == 0:
		joheaders.error_page(req, _(u'Word %i does not exist') % wid_n)
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
		if attribute[0] == 3: # integer attribute
			html_att = 'int%i' % attribute[1]
			newval_s = jotools.get_param(req, html_att, None)
			if newval_s == None: continue
			newval_s = newval_s.strip()
			if newval_s == u'':
				newval = None
			else:
				try: newval = int(newval_s)
				except ValueError: continue
				# Limit value range to prevent troubles with storing the
				# value into the database
				if newval < -1000000 or newval > 1000000: continue
			
			vresults = db.query(("select i.value from int_attribute_value i where " +
			                     "i.wid = %i and i.aid = %i") % (wid_n, attribute[1]))
			if vresults.ntuples() == 0: oldval = None
			else: oldval = vresults.getresult()[0][0]
			if oldval == newval: continue
			if not event_inserted:
				db.query("insert into event(eid, eword, euser) values(%i, %i, %i)" % \
				         (eid, wid_n, uid))
				event_inserted = True
			if newval == None:
				db.query(("delete from int_attribute_value where wid = %i " +
				          "and aid = %i") % (wid_n, attribute[1]))
			elif oldval == None:
				db.query(("insert into int_attribute_value(wid, aid, value, eevent) " +
				          "values(%i, %i, %i, %i)") % (wid_n, attribute[1],
					                             newval, eid))
			else:
				db.query(("update int_attribute_value set value=%i, eevent=%i " +
				          "where wid=%i and aid=%i") %
					(newval, eid, wid_n, attribute[1]))
			if oldval == None: oldval_s = _(u'(None)')
			else: oldval_s = `oldval`
			if newval == None: newval_s = _(u'(None)')
			else: newval_s = `newval`
			messages.append(u"%s: %s -> %s" % (unicode(attribute[2], 'UTF-8'),
			                oldval_s, newval_s))
	
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
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if wid == None:
		joheaders.error_page(req, _(u'Parameter %s is required') % u'wid')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u'Word %i does not exist') % wid_n)
		return '\n'
	wordinfo = results.getresult()[0]
	if req.method == 'GET': # show editor
		word = unicode(wordinfo[0], 'UTF-8')
		classid = wordinfo[1]
		title1 = _(u'Word') + u': ' + word
		link1 = u'edit?wid=%i' % wid_n
		title2 = _(u'flags')
		joheaders.page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid_n)
		jotools.write(req, u'<p>%s</p>\n' % joeditors.call(db, u'word_class', [classid]))
		jotools.write(req, joeditors.call(db, u'flag_edit_form', [wid_n, classid]))
		joheaders.page_footer_plain(req)
		return '\n'
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only GET and POST requests are allowed'))
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
			messages.append(_(u"Flag removed: '%s'") % unicode(attribute[1], 'UTF-8'))
		if newval == True:
			db.query(("insert into flag_attribute_value(wid, aid, eevent) " +
			          "values(%i, %i, %i)") % (wid_n, attribute[0], eid))
			messages.append(_(u"Flag added: '%s'") % unicode(attribute[1], 'UTF-8'))
	
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
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if wid == None:
		joheaders.error_page(req, _(u'Parameter %s is required') % u'wid')
		return '\n'
	wid_n = jotools.toint(wid)
	db = jodb.connect()
	results = db.query("select word, class from word where wid = %i" % wid_n)
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u'Word %i does not exist') % wid_n)
		return '\n'
	wordinfo = results.getresult()[0]
	if req.method == 'GET': # show editor
		word = unicode(wordinfo[0], 'UTF-8')
		classid = wordinfo[1]
		title1 = _(u'Word') + u': ' + word
		link1 = u'edit?wid=%i' % wid_n
		title2 = _(u'related words')
		joheaders.page_header_navbar_level2(req, title1, link1, title2, uid, uname, wid_n)
		jotools.write(req, u'<p>%s</p>\n' % joeditors.call(db, u'word_class', [classid]))
		jotools.write(req, joeditors.call(db, u'rwords_edit_form', [wid_n]))
		joheaders.page_footer_plain(req)
		return '\n'
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only GET and POST requests are allowed'))
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
		db.query("delete from related_word where wid = %i and rwid = %i" \
		         % (wid_n, attribute[0]))
		messages.append(_(u"Alternative spelling removed: '%s'") \
		                % jotools.escape_html(unicode(attribute[1], 'UTF-8')))
	
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
		messages.append(_(u"Alternative spelling added: '%s'") % jotools.escape_html(word))
	
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

# Returns a html class selector for a list of classes in form (cid, description). If cid != None,
# then that class is already selected (as a hidden field). Row is the number of editable row
# in the table. If include_no_class is True, then it will be possible to choose class 0
# (invalid word).
def _get_class_selector(classlist, cid, row, include_no_class):
	if cid == None and row != -1:
		retstr = u''
		for res in classlist:
			retstr = retstr + (u'<label><input type="radio" name="class%i" ' +
			                   u'value="%i">%s</input></label>') \
			         % (row, res[0], jotools.escape_html(unicode(res[1], 'UTF-8')))
		if include_no_class:
			retstr = retstr + (u'<label><input type="radio" name="class%i" ' +
			    'value="0">%s</input></label>') % (row, _(u'reject'))
		return retstr
	else:
		for res in classlist:
			if res[0] == cid:
				return (u'<input type="hidden" name="class%i" value="%i" />' +
			                  u'%s') % (row, cid,
				        jotools.escape_html(unicode(res[1], 'UTF-8')))
		return u'&nbsp;'

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
	confirm_column = False
	for word in words:
		if word['try_again'] == True:
			confirm_column = True
			break
	i = 0
	for word in words:
		jotools.write(req, u'<tr><td>')
		if word['try_again']:
			if word['oword'] != None:
				jotools.write(req, u'<input type="hidden" name="origword%i" value=%s />' \
				                   % (i, jotools.escape_form_value(word['oword'])))
			jotools.write(req, u'<input type="hidden" name="word%i" value=%s />%s</td><td>' \
			                   % (i, jotools.escape_form_value(word['word']), 
				               jotools.escape_html(word['word'])))
			incnocls = word['oword'] != None
			jotools.write(req, _get_class_selector(class_res, word['cid'], i, incnocls))
			jotools.write(req, u'<td><input type="checkbox" name="confirm%i"></td><td>' % i)
			jotools.write(req, word['error'])
			jotools.write(req, u'</td>')
			i = i + 1
		else:
			jotools.write(req, jotools.escape_html(word['word']))
			jotools.write(req, u'</td><td>')
			jotools.write(req, _get_class_selector(class_res, word['cid'], -1, False))
			jotools.write(req, u'</td><td>')
			if confirm_column: jotools.write(req, u'&nbsp;</td><td>')
			jotools.write(req, word['error'])
			jotools.write(req, u'</td>')
		jotools.write(req, u'</tr>\n')

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
	if len(h) == 0: return u''
	else: return _(u'Homonyms') + u': ' + h

# Stores a new word into the database and marks the original in raw_words as processed
# (if needed). Returns (wid, add_entry_structure) where wid is the identifier for
# the new word (or None if nothing was added) and add_entry_structure is a tuple
# for _add_entry containing the description of a word that needs confirmation from
# user before being added (or None if no confirmation is needed).
#def _store_word(db, word, oword, wclass, dupl_confirmed, uid):
def _store_word(db, word, uid):
	if word['try_again'] == False: return word
	retval = {'word': word['word'], 'oword': word['oword'], 'cid': word['cid'], 'confirmed': False,
	          'wid': None, 'error': None}
	if not jotools.checkword(word['word']):
		retval['wid'] = None
		retval['error'] = _(u'Forbidden characters in the word')
		retval['try_again'] = False
		return retval
	if word['cid'] == None:
		retval['wid'] = None
		retval['error'] = _(u'Word class must be set')
		retval['try_again'] = True
		return retval
	if word['cid'] != 0:
		if not word['confirmed']:
			homonyms = _list_homonyms(db, word['word'])
			if len(homonyms) > 0:
				retval['wid'] = None
				retval['error'] = homonyms
				retval['try_again'] = True
				return retval
		retval['wid'] = db.query("SELECT nextval('word_wid_seq')").getresult()[0][0]
		db.query("INSERT INTO word(wid, word, class, cuser) VALUES(%i, '%s', %i, %i)" \
		         % (retval['wid'], jotools.escape_sql_string(retval['word']),
		            retval['cid'], uid))
		retval['error'] = u'<a href="edit?wid=%i">%s</a>' % (retval['wid'], _(u'Word added'))
	if word['oword'] != None:
		db.query("UPDATE raw_word SET processed = TRUE WHERE word = '%s'" \
		         % jotools.escape_sql_string(word['oword']))
		if retval['error'] == None:
			retval['error'] = _(u'Word removed from the list of candidate words')
	retval['try_again'] = False
	if retval['error'] == None: retval['error'] = _(u'Nothing was done')
	return retval

def add_from_db(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if req.method != 'GET':
		joheaders.error_page(req, _(u'Only GET requests are allowed'))
		return '\n'
	db = jodb.connect()
	words_per_page = 15
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
		joheaders.error_page(req, _(u'There are no words to be added'))
		return '\n'
	if results.ntuples() == 0 and category != None:
		joheaders.error_page(req, _(u'There are no words to be added') + u' ' +
		          _(u'in category %s') % jotools.escape_html(category))
		return '\n'
	class_res = db.query("select classid, name from wordclass").getresult()
	joheaders.page_header_navbar_level1(req, _(u"Add words"), uid, uname)
	jotools.write(req, u'<form method="post" action="add">\n')
	jotools.write(req, u'<table class="border">\n')
	jotools.write(req, u'<tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
	                   % (_(u'Word'), _(u'Word class'), _(u'Notes')))
	i = 0
	for result in results.getresult():
		word = unicode(result[0], 'UTF-8')
		notes = unicode(result[1], 'UTF-8')
		jotools.write(req, u'<tr><td><input type="hidden" name="origword%i" value=%s />' \
			                   % (i, jotools.escape_form_value(word)))
		jotools.write(req, u'<input type="text" name="word%i" value=%s /></td><td>' \
		                   % (i, jotools.escape_form_value(word)))
		jotools.write(req, _get_class_selector(class_res, None, i, True))
		jotools.write(req, u'</td><td>')
		jotools.write(req, jotools.escape_html(notes))
		jotools.write(req, u'</td></tr>\n')
		i = i + 1
	jotools.write(req, u'</table>\n' +
	                   u'<p><input type="submit" value="%s"></p></form>\n' % _(u"Add words"))
	joheaders.page_footer_plain(req)
	return '\n'

def add_manual(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	if req.method != 'GET':
		joheaders.error_page(req, _(u'Only GET requests are allowed'))
		return '\n'
	db = jodb.connect()
	words_per_page = 15
	joheaders.page_header_navbar_level1(req, _(u"Add words"), uid, uname)
	jotools.write(req, u'<form method="post" action="add">\n' +
	                   u'<table class="border">\n<tr><th>%s</th><th>%s</th></tr>\n' \
	                   % (_(u'Word'), _(u'Word class')))
	_add_entry_fields(req, db, None, words_per_page)
	jotools.write(req, u'</table>\n' +
	                   u'<p><input type="submit" value="%s"></p></form>\n' % _(u"Add words"))
	joheaders.page_footer_plain(req)
	return '\n'

def add(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	db = jodb.connect()
	if req.method != 'POST':
		joheaders.error_page(req, _(u'Only POST requests are allowed'))
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
		word = {'word': nword, 'try_again': True, 'confirmed': False, 'wid': None}
		word['oword'] = jotools.get_param(req, 'origword%i' % i, None)
		nclass = jotools.get_param(req, 'class%i' % i, None)
		if not nclass in [None, u'']: nclass = jotools.toint(nclass)
		else: nclass = None
		word['cid'] = nclass
		if confirm and nclass != 0 and jotools.get_param(req, 'confirm%i' % i, u'') != u'on':
			word['error'] = _(u'Word was not added')
			word['try_again'] = False
		if jotools.get_param(req, 'confirm%i' % i, u'') == u'on': word['confirmed'] = True
		stored_word = _store_word(db, word, uid)
		if stored_word['wid'] != None: added_count = added_count + 1
		if stored_word['try_again']: need_confirm_count = need_confirm_count + 1
		nwordlist.append(stored_word)
	db.query("COMMIT")
	joheaders.page_header_navbar_level1(req, _(u"Add words"), uid, uname)
	if need_confirm_count > 0:
		jotools.write(req, u'<p>' + _(u'''Adding some words failed or requires confirmation.
Make the required changes and mark the words that you still want to add.''') + u'</p>')
		jotools.write(req, u'<form method="post" action="add">\n')
		jotools.write(req,
		  u'<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
		  % (_(u'Word'), _(u'Word class'), _(u'Confirm addition'), _(u'Notes')))
		_add_entry_fields(req, db, nwordlist, None)
		jotools.write(req, u'</table>\n<p>' +
		                   u'<input type="hidden" name="confirm" value="on">' +
		                   u'<input type="submit" value="%s"></p></form>\n' % _(u'Continue'))
		joheaders.page_footer_plain(req)
		return '\n'
	else:
		jotools.write(req, u'<p>%s:</p>' % _(u'The following changes were made'))
		jotools.write(req,
		  u'<table class="border"><tr><th>%s</th><th>%s</th><th>%s</th></tr>\n' \
		  % (_(u'Word'), _(u'Word class'), _(u'Notes')))
		_add_entry_fields(req, db, nwordlist, None)
		jotools.write(req, u'</table>\n')
		jotools.write(req, u'<p><a href="../">%s ...</a></p>\n' \
		                   % _(u'Back to main page'))
		joheaders.page_footer_plain(req)
		return '\n'

def categories(req):
	(uid, uname, editable) = jotools.get_login_user(req)
	if not editable:
		joheaders.error_page(req, _(u'You are not allowed to edit data'))
		return '\n'
	db = jodb.connect()
	results = db.query("SELECT coalesce(info, ''), count(*) FROM raw_word " +
	                   "WHERE processed = FALSE " +
	                   "GROUP BY coalesce(info, '') " +
	                   "ORDER BY coalesce(info, '') ")
	if results.ntuples() == 0:
		joheaders.error_page(req, _(u'There are no words to be added'))
		return '\n'
	joheaders.page_header_navbar_level1(req, _(u"Add words"), uid, uname)
	jotools.write(req, u"<p>%s:</p>\n" \
	                   % _(u'Choose a category from which you want to add words'))
	jotools.write(req, u"<table><tr><th>%s</th><th>%s</th></tr>\n" \
	                   % (_(u'Category'), _(u'Words left')))
	for result in results.getresult():
		cat = unicode(result[0], 'UTF-8')
		if cat == u'': cats = u'(' + _(u'no category') + u')'
		else: cats = cat
		jotools.write(req, (u'<tr><td><a href="add_from_db?category=%s">%s</a></td>' +
		                    u'<td>%i</td></tr>\n') \
		  % (jotools.escape_url(result[0]), jotools.escape_html(cats), result[1]))
	jotools.write(req, u"</table>\n")
	jotools.write(req, u'<p><a href="add_from_db">%s ...</a></p>\n' % _(u'All words'))
	joheaders.page_footer_plain(req)
	return '\n'
